import argparse
import json
import os
from pathlib import Path

from meilisearch import Client
from meilisearch.errors import MeilisearchApiError

DEFAULT_SEARCHABLE_ATTRIBUTES = [
   "科目名",
   "担当者氏名",
   "授業計画_text",
   "テキスト_text",
   "参考文献_text",
   "full_text",
   "部門"
]

DEFAULT_FILTERABLE_ATTRIBUTES = [
   "risyunen",
   "semekikn",
   "kougicd",
   "crclumcd",
   "講義学期",
   "年次",
   "担当者氏名",
   "必選区分",
   "部門"
]

DEFAULT_SORTABLE_ATTRIBUTES = [
   "更新日時",
   "科目名",
]

DEFAULT_DISPLAYED_ATTRIBUTES = [
   "id",
   "kougicd",
   "科目名",
   "担当者氏名",
   "講義学期",
   "年次",
   "更新日時",
   "fields",
   "lists",
   "部門",
]

DEFAULT_TYPO_TOLERANCE = {
   "disableOnAttributes": ["id", "kougicd"],
}


def normalize_text(value) -> str:
   return " ".join(str(value).split())


def build_list_text(list_data: dict) -> str:
   items = list_data.get("items", []) if isinstance(list_data, dict) else []
   chunks = []
   for item in items:
      if not isinstance(item, dict):
         continue
      ordered_values = []
      if "no" in item:
         ordered_values.append(str(item.get("no")))
      for key, value in item.items():
         if key == "no":
            continue
         ordered_values.append(str(value))
      text = normalize_text(" ".join(ordered_values))
      if text:
         chunks.append(text)
   return " ".join(chunks)


def transform_document(doc: dict) -> dict | None:
   if not isinstance(doc, dict):
      return None

   doc_id = doc.get("id")
   if doc_id in (None, ""):
      return None

   fields = doc.get("fields") if isinstance(doc.get("fields"), dict) else {}
   lists = doc.get("lists") if isinstance(doc.get("lists"), dict) else {}

   transformed = {
      "id": doc_id,
      "fields": fields,
      "lists": lists,
   }

   # Preserve existing top-level scalar keys if they already exist.
   for key, value in doc.items():
      if key in ("fields", "lists"):
         continue
      transformed[key] = value

   # Promote fields to top-level searchable attributes.
   for key, value in fields.items():
      transformed[key] = normalize_text(value)

   # Convert nested lists to searchable text fields, e.g. 授業計画_text.
   for label, list_data in lists.items():
      list_text = build_list_text(list_data)
      transformed[f"{label}_text"] = list_text

   searchable_chunks = []
   for key, value in transformed.items():
      if key in ("id", "fields", "lists"):
         continue
      if isinstance(value, str):
         cleaned = normalize_text(value)
         if cleaned:
            searchable_chunks.append(cleaned)

   transformed["full_text"] = " ".join(searchable_chunks)
   return transformed


def discover_json_files(target_dir: Path) -> list[Path]:
   return sorted(p for p in target_dir.rglob("*.json") if p.is_file())


def load_documents_from_json(path: Path) -> list[dict]:
   with path.open("r", encoding="utf-8") as f:
      data = json.load(f)

   if isinstance(data, list):
      docs = [x for x in data if isinstance(x, dict)]
   elif isinstance(data, dict):
      docs = [data]
   else:
      docs = []

   valid_docs = []
   for doc in docs:
      transformed = transform_document(doc)
      if transformed is None:
         continue
      valid_docs.append(transformed)
   return valid_docs


def chunked(items: list[dict], batch_size: int):
   for i in range(0, len(items), batch_size):
      yield items[i : i + batch_size]


def get_task_uid(task_obj):
   if task_obj is None:
      return None
   if isinstance(task_obj, dict):
      return task_obj.get("taskUid") or task_obj.get("task_uid")
   return getattr(task_obj, "task_uid", None) or getattr(task_obj, "taskUid", None)


def get_task_status(task_obj):
   if task_obj is None:
      return None
   if isinstance(task_obj, dict):
      return task_obj.get("status")
   return getattr(task_obj, "status", None)


def main():
   parser = argparse.ArgumentParser(description="Initialize Meilisearch settings and import all JSON files in a folder")
   parser.add_argument("target_dir", help="Target directory that contains JSON files")
   parser.add_argument("--host", default=os.getenv("MEILI_HOST", "http://127.0.0.1:7700"), help="Meilisearch host URL")
   parser.add_argument("--api-key", default=os.getenv("MEILI_MASTER_KEY"), help="Meilisearch API key")
   parser.add_argument("--index", default="syllabus", help="Index UID")
   parser.add_argument("--batch-size", type=int, default=500, help="Number of documents per upload batch")
   parser.add_argument("--no-wait", action="store_true", help="Do not wait for async Meilisearch tasks")
   args = parser.parse_args()

   target_dir = Path(args.target_dir)
   if not target_dir.exists() or not target_dir.is_dir():
      raise SystemExit(f"Target directory does not exist or is not a directory: {target_dir}")

   client = Client(args.host, args.api_key)

   def ensure_index(index_uid: str, primary_key: str = "id"):
      try:
         client.get_index(index_uid)
         return None
      except MeilisearchApiError:
         task = client.create_index(index_uid, {"primaryKey": primary_key})
         return get_task_uid(task)

   def update_settings(index_uid: str):
      index = client.index(index_uid)
      payload = {
         "searchableAttributes": DEFAULT_SEARCHABLE_ATTRIBUTES,
         "filterableAttributes": DEFAULT_FILTERABLE_ATTRIBUTES,
         "sortableAttributes": DEFAULT_SORTABLE_ATTRIBUTES,
         "displayedAttributes": DEFAULT_DISPLAYED_ATTRIBUTES,
         "typoTolerance": DEFAULT_TYPO_TOLERANCE,
      }
      task = index.update_settings(payload)
      return get_task_uid(task)

   def add_documents(index_uid: str, docs: list[dict]):
      index = client.index(index_uid)
      task = index.add_documents(docs)
      return get_task_uid(task)

   def wait_task(task_uid: int):
      task = client.wait_for_task(task_uid, timeout_in_ms=300000, interval_in_ms=500)
      return task

   setup_tasks = []
   task_uid = ensure_index(args.index, primary_key="id")
   if task_uid is not None:
      setup_tasks.append(task_uid)
      print(f"Index creation task queued: {task_uid}")

   settings_task = update_settings(args.index)
   if settings_task is not None:
      setup_tasks.append(settings_task)
      print(f"Settings update task queued: {settings_task}")

   if not args.no_wait:
      for uid in setup_tasks:
         task = wait_task(uid)
         if get_task_status(task) != "succeeded":
               raise RuntimeError(f"Setup task failed: {task}")

   json_files = discover_json_files(target_dir)
   print(f"Discovered JSON files: {len(json_files)}")

   all_docs = []
   skipped_files = 0
   for file_path in json_files:
      docs = load_documents_from_json(file_path)
      if not docs:
         skipped_files += 1
         continue
      all_docs.extend(docs)

   if not all_docs:
      print("No valid documents found. Done.")
      return

   print(f"Valid documents to upload: {len(all_docs)}")
   upload_tasks = []
   for batch in chunked(all_docs, max(args.batch_size, 1)):
      uid = add_documents(args.index, batch)
      if uid is not None:
         upload_tasks.append(uid)

   print(f"Upload tasks queued: {len(upload_tasks)}")
   if not args.no_wait:
      for uid in upload_tasks:
         task = wait_task(uid)
         if get_task_status(task) != "succeeded":
               raise RuntimeError(f"Upload task failed: {task}")

   print("Completed")
   print(f"Skipped JSON files (no valid docs): {skipped_files}")


if __name__ == "__main__":
   main()

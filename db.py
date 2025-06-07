import pathlib
import json
import pandas as pd
from app_config import crawl_config


class DB:
    def __init__(self):
        self.profile_path = "db/profile.csv"
        self.statistic_path = "db/statistic.json"
        self.dataset_dir_path = "db/dataset"
        self.init_all_files()

    def get_dataset_path(self, category):
        if category == "software":
            return f'{self.dataset_dir_path}/software'
        elif category == "BA":
            return f'{self.dataset_dir_path}/ba'
        elif category == "PM":
            return f'{self.dataset_dir_path}/pm'
        elif category == "UX/UI":
            return f'{self.dataset_dir_path}/uxui'
        elif category == "AI":
            return f'{self.dataset_dir_path}/ai'
        elif category == "tester":
            return f'{self.dataset_dir_path}/tester'
        elif category == "devops":
            return f'{self.dataset_dir_path}/devops'
        elif category == "HR":
            return f'{self.dataset_dir_path}/hr'

    def get_category(self, search_name):
        if search_name == crawl_config["category"][0]:
            return f'software'
        elif search_name == crawl_config["category"][1]:
            return f'BA'
        elif search_name == crawl_config["category"][2]:
            return f'PM'
        elif search_name == crawl_config["category"][3]:
            return f'UX/UI'
        elif search_name == crawl_config["category"][4]:
            return f'AI'
        elif search_name == crawl_config["category"][5]:
            return f'tester'
        elif search_name == crawl_config["category"][6]:
            return f'devops'
        elif search_name == crawl_config["category"][7]:
            return f'HR'

    def init_all_files(self):
        statistic_file = pathlib.Path(self.statistic_path)
        profile_file = pathlib.Path(self.profile_path)
        dataset_dir_path = pathlib.Path(self.dataset_dir_path)

        if not statistic_file.exists():
            with open(self.statistic_path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)

        if not profile_file.exists():
            df = pd.DataFrame(columns=["Link"])
            df.to_csv(self.profile_path, index=False, encoding="utf-8")

        if not dataset_dir_path.exists() and dataset_dir_path.is_dir():
            dataset_dir_path.mkdir(parents=True, exist_ok=True)

    def load_statistic(self):
        with open(self.statistic_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def update_statistic(self, data):
        with open(self.statistic_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def update_crawl_num(self):
        statistic = self.load_statistic()
        statistic["crawled_index"] = int(statistic["crawled_index"]) + 1
        self.update_statistic(statistic)

    def update_crawl_page(self, category, name, page):
        statistic = self.load_statistic()
        print(category, "::::::::::::::::::::")
        statistic[f"{category}_{name}"] = page
        self.update_statistic(statistic)

    def get_crawl_page(self, category, name):
        statistic = self.load_statistic()
        key = f"{category}_{name}"
        return int(statistic.get(key, 0))

    def load_profiles(self):
        df = pd.read_csv(self.profile_path)
        return df

    def update_profiles(self, data):
        df = pd.DataFrame(data)
        df.to_csv(self.profile_path, index=False, encoding="utf-8")

    def add_profile(self, profile_url, category):
        data = self.load_profiles()
        if profile_url not in data['Link'].values:
            new_row = pd.DataFrame([{"Link": profile_url, "Category": category}])
            data = pd.concat([data, new_row], ignore_index=True)
            self.update_profiles(data)
            return True
        return False

    def get_needed_profiles(self, crawl_num):
        statistic = self.load_statistic()
        crawled_number = statistic.get("crawled_index", -1)
        data = self.load_profiles()
        start = crawled_number + 1
        end = start + crawl_num
        return data.iloc[start:end].to_dict(orient="records")

db = DB()
print(db.get_category("business analyst"))
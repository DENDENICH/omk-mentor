import pandas as pd
from pandas import DataFrame

from groups.exceptions import FileException, InvalidDataException


class ExcelGroupParser:

    REQUIRED_COLUMNS = {
        "Табельный номер",
        "Роль",
        "Табельный номер наставника"
    }

    ROLE_MAP = {
        "Организатор": "organizer",
        "Наставник": "mentor",
        "Студент": "student"
    }

    def parse(self, file, file_name: str) -> dict:
        
        df = self._checking_columns(file)

        members = []
        organizer = None

        for idx, row in df.iterrows():
            role_raw = str(row["Роль"]).strip()
            role = self.ROLE_MAP.get(role_raw)

            if not role:
                raise ValueError(f"Неверная роль '{role_raw}' в строке {idx + 2}")

            tab = str(row["Табельный номер"]).strip()
            mentor_tab = (
                str(row["Табельный номер наставника"]).strip()
                if pd.notna(row["Табельный номер наставника"])
                else ""
            )

            item = {
                "tab": tab,
                "role": role,
                "mentor_tab": mentor_tab or None
            }

            if role == "organizer":
                organizer = item
            else:
                members.append(item)

        if not organizer:
            raise ValueError("В Excel не указан организатор")

        return {
            "group_name": file_name.split(".")[0],
            "organizer": organizer,
            "members": members,
        }
    
    def _checking_columns(self, file) -> DataFrame:
        """
        Checking column in file
        """
        try:
            df = pd.read_excel(file, engine="openpyxl")
        except Exception as e:
            raise FileException("Ошибка при чтении Excel")

        if not self.REQUIRED_COLUMNS.issubset(df.columns):
            missing = self.REQUIRED_COLUMNS - set(df.columns)
            raise InvalidDataException(f"Отсутствуют колонки: {missing}")
        return df

    

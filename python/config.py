import os
from pathlib import Path

class Config:
    def __init__(self, file, dbpath="../../prundb/prundb.db"):
        script_dir = Path(file).resolve().parent
        os.chdir(script_dir)

        relative = Path(dbpath)
        self.resolved_dbfile = relative.resolve()
    
    def get_dbpath(self):
        return self.resolved_dbfile

    def get_connection_uri(self):
        return f"sqlite:///{self.resolved_dbfile}"

if __name__ == "__main__":
    cfg = Config(__file__)
    print(cfg.get_connection_uri())
    print(cfg.get_dbpath())
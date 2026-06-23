import os
from pathlib import Path

class Config:
    def __init__(self, file, dbpath="../../prundb/prundb.db"):
        self.file = file
        self.dbpath = dbpath
    
    def get_dbpath(self):
        return self.dbpath

    def get_connection_uri(self):
        
        script_dir = Path(self.file).resolve().parent
        os.chdir(script_dir)

        relative = Path(self.dbpath)
        dbfile = relative.resolve()

        return f"sqlite:///{dbfile}"

if __name__ == "__main__":
    cfg = Config(__file__)
    print(cfg.get_connection_uri())
## Quickstart

For Linux only. If you're a Windows user, consider installing WSL so you have a Linux environment available.

1. Run `./setup.sh`, follow any instructions
1. Install crontab (`crontab -e`) based on sample crontab (`crontab.example`). You may need to set your path to the `.venv/bin` directory
1. Run `source .venv/bin/activate` before running any scripts

## Scripts

* `book_viewer.py`: A script which is to be run in a terminal. Allows you to see the order book over a period of time. Uses local sqlite database for history, must have crontab setup beforehand
* `analysis.ipynb`: A jupyter notebook that you can use to look through the dataframes that the libraries provide. VSCode is a way to use the notebook

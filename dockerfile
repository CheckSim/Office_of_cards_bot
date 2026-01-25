FROM conda/miniconda3

RUN mkdir data

WORKDIR /data

COPY ./environment.yml .

RUN conda update conda
RUN conda config --prepend channels conda-forge
RUN conda config --set channel_priority strict
RUN conda env create -f environment.yml
SHELL ["conda", "run", "-n", "OOC", "/bin/bash", "-c"]

COPY ./Bot_10.py .
COPY ./constants.py .
COPY ./keys.py .
RUN mkdir data
COPY ./data/db.csv ./data/db.csv
COPY ./data/episode.csv ./data/episode.csv
COPY ./data/pills.csv ./data/pills.csv
COPY ./data/stats.csv ./data/stats.csv

ENTRYPOINT ["conda", "run", "-n", "OOC", "python3", "Bot_10.py"]

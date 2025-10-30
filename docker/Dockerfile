ARG BASE_IMAGE=housing-crisis-base:latest
FROM $BASE_IMAGE

SHELL ["conda", "run", "-n", "housing_ml_env", "/bin/bash", "-c"]

COPY docker/condaEnv-ml.yml /tmp/environment-ml.yml
RUN conda env update --file /tmp/environment-ml.yml && conda clean -afy

RUN pip install --no-cache-dir \
    torch-scatter torch-sparse torch-cluster torch-spline-conv \
    -f https://data.pyg.org/whl/torch-2.1.0+cu121.html

RUN pip install --no-cache-dir torch-geometric==2.5.0

RUN pip install --no-cache-dir \
    git+https://github.com/google-research/timesfm.git@main

RUN pip install --no-cache-dir \
    git+https://github.com/amazon-science/chronos-forecasting.git@main

WORKDIR /app

COPY src /app/src
COPY config /app/config
COPY main.py /app/main.py
COPY setup.py /app/setup.py

RUN pip install --no-cache-dir -e .

ENV PYTHONPATH=/app:$PYTHONPATH

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "housing_ml_env", "/entrypoint.sh"]
CMD ["serve"]

FROM langchain/langgraph-api:3.11







# -- Installing local requirements --
ADD requirements.txt /deps/__outer_backend/src/requirements.txt

RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir -c /api/constraints.txt -r /deps/__outer_backend/src/requirements.txt
# -- End of local requirements install --



# -- Adding non-package dependency backend --
ADD . /deps/__outer_backend/src
RUN set -ex && \
    for line in '[project]' \
                'name = "backend"' \
                'version = "0.1"' \
                '[tool.setuptools.package-data]' \
                '"*" = ["**/*"]' \
                '[build-system]' \
                'requires = ["setuptools>=61"]' \
                'build-backend = "setuptools.build_meta"'; do \
        echo "$line" >> /deps/__outer_backend/pyproject.toml; \
    done
# -- End of non-package dependency backend --



# -- Installing all local dependencies --

RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir -c /api/constraints.txt -e /deps/*

# -- End of local dependencies install --

ENV LANGGRAPH_HTTP='{"app": "/deps/__outer_backend/src/main.py:app"}'

ENV LANGSERVE_GRAPHS='{"support_agent": "/deps/__outer_backend/src/src/workflow/graph.py:graph"}'







# -- Ensure user deps didn't inadvertently overwrite langgraph-api
RUN mkdir -p /api/langgraph_api /api/langgraph_runtime /api/langgraph_license && touch /api/langgraph_api/__init__.py /api/langgraph_runtime/__init__.py /api/langgraph_license/__init__.py
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir --no-deps -e /api
# -- End of ensuring user deps didn't inadvertently overwrite langgraph-api --
# -- Removing build deps from the final image ~<:===~~~ --
RUN pip uninstall -y pip setuptools wheel
RUN rm -rf /usr/local/lib/python*/site-packages/pip* /usr/local/lib/python*/site-packages/setuptools* /usr/local/lib/python*/site-packages/wheel* && find /usr/local/bin -name "pip*" -delete || true
RUN rm -rf /usr/lib/python*/site-packages/pip* /usr/lib/python*/site-packages/setuptools* /usr/lib/python*/site-packages/wheel* && find /usr/bin -name "pip*" -delete || true
RUN uv pip uninstall --system pip setuptools wheel && rm /usr/bin/uv /usr/bin/uvx



WORKDIR /deps/__outer_backend/src
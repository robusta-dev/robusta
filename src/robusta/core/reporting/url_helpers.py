import logging
from typing import Optional
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse

from robusta.core.model.env_vars import ROBUSTA_UI_DOMAIN


PROM_GRAPH_PATH_URL: str = "/graph"
PROM_GRAPH_URL_EXPR_PARAM: str = "g0.expr"


def convert_prom_graph_url_to_robusta_metrics_explorer(prom_url: str, cluster_name: str, account_id: str) -> str:
    try: 
        parsed_url: ParseResult = urlparse(prom_url)
        if parsed_url.path != PROM_GRAPH_PATH_URL:
            logging.warning("Failed to convert to robusta metric explorer url, url: %s not seems to be graph url", prom_url)
            return prom_url

        query_string = parse_qs(parsed_url.query)
        expr_params: Optional[list[str]] = query_string.get(PROM_GRAPH_URL_EXPR_PARAM)
        if not expr_params:
            logging.warning("Failed to get expr params, url: %s not seems to be graph url", prom_url)
            return prom_url

        expr = expr_params[0]
        params: dict[str, str] = {"query": expr, "cluster": cluster_name, "account": account_id}
        robusta_metrics_url: str = f"{ROBUSTA_UI_DOMAIN}/metrics-explorer?{urlencode(params)}"
        return robusta_metrics_url
    except Exception:
        logging.warning('Failed to convert prom url: %s to robusta url', prom_url, exc_info=True)
        return prom_url

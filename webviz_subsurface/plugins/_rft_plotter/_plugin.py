from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from dash import html
from webviz_config import WebvizPluginABC, WebvizSettings

from ._business_logic import RftPlotterDataModel
from ._plugin_ids import PluginIds
from ._views import (
    ParameterResponseView,
    RftCrossplot,
    RftMap,
    RftMisfitPerObservation,
    RftMisfitPerReal,
)


class RftPlotter(WebvizPluginABC):
    """This plugin visualizes simulated RFT results from
    FMU ensembles combined with ERT observation data.

    Several visualizations are available:

    * Map view of RFT observations.

    * Depth vs pressure plot showing simulated RFT data along wells together
    with observation points.

    * Barchart showing sum of mean misfit for ERT observations per realization.
    One plot per ensemble.

    * Crossplot of simulated RFT vs observed value per ERT observation. One plot per ensemble.

    * Boxplot showing misfit per ERT observation for each ensemble.

    * Plots for analysing the parameter response of the RFT data. Not available for aggregated data.

    ---
    **Using data per realization**

    * **`ensembles`**: Which ensembles in `shared_settings` to visualize.

    In addition, you need to have rft-files in your realizations stored at the local path \
    `share/results/tables`. The `rft_ert.csv` is required as input, while the `rft.csv` is optional:

    * **`rft_ert.csv`**: A csv file containing simulated and observed RFT data for RFT observations
    defined in ERT \
    [(example file)](https://github.com/equinor/webviz-subsurface-testdata/blob/master/\
    01_drogon_ahm/realization-0/iter-0/share/results/tables/rft_ert.csv).

    * **`rft.csv`**:
    A csv file containing simulated RFT data extracted from ECLIPSE RFT output files \
    using [ecl2df](https://equinor.github.io/ecl2df/ecl2df.html#module-ecl2df.rft) \
    [(example file)](https://github.com/equinor/webviz-subsurface-testdata/blob/master/\
    01_drogon_ahm/realization-0/iter-0/share/results/tables/rft.csv). \
    Simulated RFT data can be visualized along MD if a "CONMD" column is present in \
    the dataframe and only for wells where each RFT datapoint has a unique MD.

    * **`parameters.txt`**: File with parameters and values

    **Using aggregated data**

    * **`csvfile_rft`**: Aggregated version of `rft.csv` [(example file)](\
    https://github.com/equinor/webviz-subsurface-testdata/blob/master/reek_test_data/aggregated_data/rft.csv).
    * **`csvfile_rft_ert`**: Aggregated version of `rft_ert.csv` [(example file)](\
    https://github.com/equinor/webviz-subsurface-testdata/blob/master/reek_test_data/aggregated_data/rft_ert.csv).


    **Optional input for both input options**

    * **`obsdata`**: A csv file containing additional RFT observation data not defined in ERT for
    visualization together with simulated RFT.
    Mandatory column names: `WELL`, `DATE` (yyyy-mm-dd), `DEPTH` and `PRESSURE`

    * **`formations`**: A csv file containing top and base values for each zone per well.
    Used to visualize zone boundaries together with simulated RFT.
    Mandatory column names: `WELL`, `ZONE`, `TOP_TVD`, `BASE_TVD` \
    [(example file))](https://github.com/equinor/webviz-subsurface-testdata/blob/master/\
    01_drogon_ahm/realization-0/iter-0/share/results/tables/formations.csv).

    * **`faultlines`**:
    A csv file containing faultpolygons to be visualized together with the map view.
    Export format from [xtgeo.xyz.polygons.dataframe](
    https://xtgeo.readthedocs.io/en/latest/apiref/xtgeo.xyz.polygons.html#xtgeo.xyz.polygons.Polygons.dataframe
    ) \
    [(example file)](\
    https://github.com/equinor/webviz-subsurface-testdata/blob/master/01_drogon_ahm/\
    realization-0/iter-0/share/results/polygons/toptherys--gl_faultlines_extract_postprocess.csv).

    ---
    ?> Well name needs to be consistent with Eclipse well name.

    ?> Only RFT observations marked as active in ERT are used to generate plots.

    The `rft_ert.csv` file can be generated by running the "MERGE_RFT_ERTOBS" forward model in ERT,
    this will collect ERT RFT observations and merge with CSV output from the "GENDATA_RFT" forward
    model. [ERT docs](https://fmu-docs.equinor.com/docs/ert/reference/\
    forward_models.html?highlight=gendata_rft#MERGE_RFT_ERTOBS).

    """

    # pylint: disable=too-few-public-methods
    class Tabs:
        MISFIT_PLOT = "misfitplot"
        CROSS_PLOT = "crossplot"
        ERROR_PLOT = "errorplot"

    def __init__(
        self,
        webviz_settings: WebvizSettings,
        csvfile_rft: Path = None,
        csvfile_rft_ert: Path = None,
        ensembles: Optional[List[str]] = None,
        formations: Path = None,
        obsdata: Path = None,
        faultlines: Path = None,
    ) -> None:
        super().__init__(stretch=True)

        self._datamodel = RftPlotterDataModel(
            webviz_settings,
            ensembles,
            formations,
            faultlines,
            obsdata,
            csvfile_rft,
            csvfile_rft_ert,
        )

        self.add_view(
            RftMap(self._datamodel), PluginIds.Views.RFT_MAP, PluginIds.Views.GROUP_NAME
        )

        self.add_view(
            RftMisfitPerReal(self._datamodel, self.Tabs.MISFIT_PLOT),
            PluginIds.Views.RFT_MISFIT_PER_REAL,
            PluginIds.Views.GROUP_NAME,
        )

        self.add_view(
            RftCrossplot(self._datamodel, self.Tabs.CROSS_PLOT),
            PluginIds.Views.RFT_CROSSPLOT,
            PluginIds.Views.GROUP_NAME,
        )

        self.add_view(
            RftMisfitPerObservation(self._datamodel, self.Tabs.ERROR_PLOT),
            PluginIds.Views.RFT_MISFIT_PER_OBSERVATION,
            PluginIds.Views.GROUP_NAME,
        )

        if not self._datamodel.param_model.sensrun:
            self.add_view(
                ParameterResponseView(self._datamodel),
                PluginIds.Views.PARAMETER_RESPONSE,
                PluginIds.Views.GROUP_NAME,
            )

    def add_webvizstore(self) -> List[Tuple[Callable, List[Dict]]]:
        return self._datamodel.webviz_store

    @property
    def layout(self) -> html.Div:
        return html.Div()

    # @property
    # def tour_steps(self) -> List[dict]:
    #     return [
    #         {
    #             "id": self.view(PluginIds.Views.RFT_MAP)
    #             .layout_element(RftMap.Ids.MAP_GRAPH)
    #             .get_unique_id(),
    #             "content": """ map """
    #         },
    #         {
    #             "id": self.view(PluginIds.Views.RFT_MAP)
    #             .layout_element(RftMap.Ids.FORMATION_GRAPH)
    #             .get_unique_id(),
    #             "content": """ formation  """
    #         }
    #     ]

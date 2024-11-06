/** @odoo-module **/

import { BurndownChartModel } from "./burndown_chart_model";
import { graphView } from "@web/views/graph/graph_view";
import { registry } from "@web/core/registry";
import { BurndownChartSearchModel } from "./burndown_chart_search_model";

const viewRegistry = registry.category("views");

const thburndownChartGraphView = {
  ...graphView,
  buttonTemplate: "th_project_itc.BurndownChartView.Buttons",
  hideCustomGroupBy: true,
  Model: BurndownChartModel,
  searchMenuTypes: graphView.searchMenuTypes.filter(menuType => menuType !== "comparison"),
  SearchModel: BurndownChartSearchModel,
};

viewRegistry.add("th_burndown_chart", thburndownChartGraphView);

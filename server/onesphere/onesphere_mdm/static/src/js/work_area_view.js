odoo.define("onesphere.WorkAreaView", function (require) {
  "use strict";
  var FormView = require("web.FormView");
  var FormRenderer = require("web.FormRenderer");

  var ListView = require("web.ListView");
  var ListRenderer = require("web.ListRenderer");
  var viewRegistry = require("web.view_registry");
  var core = require("web.core");

  var _lt = core._lt;

  var WorkAreaFormRender = FormRenderer.extend({
    init: function (parent, state, params) {
      this._super.apply(this, arguments);
      this.context = state.context || state.getContext() || {};
    },
    _renderTagLabel: function (node) {
      var ret = this._super.apply(this, arguments);
      var context = this.context || {};
      if (node.tag === "field" && node.attrs.name === "name") {
        if (context.hasOwnProperty("search_default_is_shop_floor")) {
          ret.text(_lt("Shop Floor Name"));
        } else if (
          context.hasOwnProperty("search_default_is_production_line")
        ) {
          ret.text(_lt("Production Line Name"));
        } else if (context.hasOwnProperty("search_default_is_work_segment")) {
          ret.text(_lt("Work Segment Name"));
        } else if (context.hasOwnProperty("search_default_is_work_station")) {
          ret.text(_lt("Work Station Name"));
        } else if (
          context.hasOwnProperty("search_default_is_workstation_unit")
        ) {
          ret.text(_lt("Work Station Unit Name"));
        }
      }
      return ret;
    },
  });

  var WorkAreaFormView = FormView.extend({
    config: _.extend({}, FormView.prototype.config, {
      Renderer: WorkAreaFormRender,
    }),
  });

  var WorkAreaListRender = ListRenderer.extend({
    init: function (parent, state, params) {
      this._super.apply(this, arguments);
      this.context = state.context || state.getContext() || {};
    },

    _renderHeaderCell: function (node) {
      var ret = this._super.apply(this, arguments);
      var context = this.context || {};
      if (node.attrs.name === "name") {
        if (context.hasOwnProperty("search_default_is_shop_floor")) {
          ret.text(_lt("Shop Floor Name"));
        } else if (
          context.hasOwnProperty("search_default_is_production_line")
        ) {
          ret.text(_lt("Production Line Name"));
        } else if (context.hasOwnProperty("search_default_is_work_segment")) {
          ret.text(_lt("Work Segment Name"));
        } else if (context.hasOwnProperty("search_default_is_work_station")) {
          ret.text(_lt("Work Station Name"));
        } else if (
          context.hasOwnProperty("search_default_is_workstation_unit")
        ) {
          ret.text(_lt("Work Station Unit Name"));
        }
      }
      return ret;
    },
  });

  var WorkAreaTreeView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
      Renderer: WorkAreaListRender,
    }),
  });

  viewRegistry.add("onesphere_work_area_form", WorkAreaFormView);
  viewRegistry.add("onesphere_work_area_tree", WorkAreaTreeView);
});

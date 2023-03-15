odoo.define("onesphere.tightening.spc.view", function (require) {
  "use strict";

  var FormView = require("web.FormView");
  const SPCViewerController = require("onesphere.spc.controller");
  var viewRegistry = require("web.view_registry");
  var Dialog = require("web.Dialog");

  var core = require("web.core");

  var _t = core._t;
  var SPCFormRenderingEngine = require("onesphere.spc.render");
  var TighteningSPCFormController = SPCViewerController.extend({
    init: function (parent, model, renderer, params) {
      this._super.apply(this, arguments);
    },

    _onButtonQuerySPC: function (ev) {
      var self = this;
      var bolt_id = self.renderer.state.data["bolt_id"];
      var query_date_from = self.renderer.state.data["query_date_from"];
      var query_date_to = self.renderer.state.data["query_date_to"];
      var query_type = self.renderer.state.data["measurement_type"] || "torque";
      var usl = self.renderer.state.data["usl"] || 10.0;
      var lsl = self.renderer.state.data["lsl"] || 1.0;
      var limit = self.renderer.state.data["limit"] || 1000;
      var diff = query_date_to.diff(query_date_from);
      if (diff <= 0) {
        Dialog.alert(self, _t("Date Time Window Is Invalid!"), {
          title: _t("Date Time Window Is Invalid"),
        });
        return;
      }
      var dd = _.map(
        this.renderer.state.fieldsInfo[this.viewType],
        function (val, field_name) {
          var required = val.required;
          if (!!!required) {
            //非必填一定是有效
            return { field: field_name, isValid: true };
          }
          return {
            field: field_name,
            isValid: required && self.renderer.state.data[field_name],
          };
        }
      );
      try {
        var d = _.find(dd, function (v) {
          return !v.isValid; //返回第一个无效
        });
        if (!!d) {
          Dialog.alert(self, _t("Field Required: ") + d.field, {
            title: _t("Field Required"),
          });
          return;
        }
      } catch (error) {
        console.error(error);
      }
      var others = {
        model_object: self.renderer.state.data["model_object"],
        model_object_field: self.renderer.state.data["model_object_field"],
        spc_step: self.renderer.state.data["spc_step"] || 0.1,
      };

      this._rpc({
        model: this.modelName,
        method: "query_spc",
        args: [
          bolt_id.res_id,
          query_date_from.format("YYYY-MM-DD HH:mm:ss"),
          query_date_to.format("YYYY-MM-DD HH:mm:ss"),
          query_type,
          usl,
          lsl,
          limit,
          others,
        ],
      }).then(function (result) {
        if (!!result.cmk) {
          self.setData(self.handle, "cmk", result.cmk);
        } else {
          self.setData(self.handle, "cmk", 0.0);
        }
        if (!!result.cpk) {
          self.setData(self.handle, "cpk", result.cpk);
        } else {
          self.setData(self.handle, "cpk", 0.0);
        }
        if (!!result.cp) {
          self.setData(self.handle, "cp", result.cp);
        } else {
          self.setData(self.handle, "cp", 0.0);
        }
        if (!!result.cr) {
          self.setData(self.handle, "cr", result.cr);
        } else {
          self.setData(self.handle, "cr", 0.0);
        }
        if (!!result.pages) {
          self.renderer.chartsData = result.pages;
          self.renderer.render_pages(result.pages);
          self.displayNotification({
            type: "success",
            title: result.title || "SPC分析成功",
            message: result.message || "",
            sticky: false,
          });
        } else {
          self.displayNotification({
            type: "warning",
            title: result.title || "SPC分析失败",
            message: result.message || "",
            sticky: false,
          });
        }
      });
    },
  });

  var SPCViewerRenderer = SPCFormRenderingEngine.extend({
    init: function (parent, model, renderer, params) {
      this._super.apply(this, arguments);
      this.chartsData = null;
    },

    _renderTabPage: function (page, page_id) {
      var $ret = this._super.apply(this, arguments);
      return $ret;
    },

    //         _onNotebookTabChanged: function (evt) {
    //             if (!!this.chartsData) {
    //                 this.render_pages(this.chartsData);
    //             }
    // //             var activeTab = evt;
    // //             // var tab = activeTab.get(0);
    // //             var href = activeTab.attr('href'); //為id
    // //             var ele =  $new_notebook.find(href).get(0);
    // //             var chart = echarts.getInstanceByDom(ele);
    // //             chart.resize();
    //             this._super.apply(this, arguments);
    //         },
  });
  var TighteningSPCFormView = FormView.extend({
    config: _.extend({}, FormView.prototype.config, {
      Controller: TighteningSPCFormController,
      Renderer: SPCViewerRenderer,
    }),
  });

  viewRegistry.add("tightening_spc_form", TighteningSPCFormView);

  return TighteningSPCFormView;
});

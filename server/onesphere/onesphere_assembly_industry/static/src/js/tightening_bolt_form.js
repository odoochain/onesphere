odoo.define("onesphere.tightening.bolt.view", function (require) {
  "use strict";

  const FormController = require("web.FormController");
  var core = require("web.core");
  var viewRegistry = require("web.view_registry");
  var SPCView = require("onesphere.tightening.spc.view");
  var FormView = require("web.FormView");

  var OnsephereBoltFormController = FormController.extend({
    events: _.extend({}, FormController.prototype.events, {
      "click button.o_button_process_proposal": "_onButtonProcessProposal",
    }),
    _onButtonClicked: function (ev) {
      this._super.apply(this, arguments);
      if (ev.data.attrs.class === "o_button_process_proposal") {
        this._onButtonProcessProposal(ev);
      }
    },
    _onButtonProcessProposal: function (ev) {
      var self = this;
      this._rpc({
        model: ev.data.record.model,
        method: "button_open_tightening_process_proposal_analysis",
        args: [[ev.data.record.res_id]],
      }).then(function (result) {
        if (!!result.pages) {
          self.renderer.chartsData = result.pages;
          self.renderer.render_pages(result.pages);
          self.renderer._clickTab("li.tightening_angle_proposal > a");
          self.displayNotification({
            type: "success",
            title: "拧紧工艺优化分析成功!!!",
            message: "请切换至下方相关优化查看标签页",
            sticky: false,
          });
        }
      });
    },
  });

  var OnsephereBoltFormRenderer = SPCView.prototype.config.Renderer.extend({
    _clickTab: function (selection) {
      var self = this;
      if (!!!selection) {
        return;
      }
      var ele = self.$el.find(selection);
      if (ele) {
        ele.click();
      }
    },

    _onNotebookTabChanged: function (evt) {
      // if (render_pages) {
      //     render_pages(chartsData);
      // }
      //             var activeTab = evt;
      //             // var tab = activeTab.get(0);
      //             var href = activeTab.attr('href'); //為id
      //             var ele =  $new_notebook.find(href).get(0);
      //             var chart = echarts.getInstanceByDom(ele);
      //             chart.resize();
      this._super.apply(this, arguments);
    },
  });

  var OnsephereBoltFormView = FormView.extend({
    config: _.extend({}, FormView.prototype.config, {
      Controller: OnsephereBoltFormController,
      Renderer: OnsephereBoltFormRenderer,
    }),
  });

  viewRegistry.add("tightening_bolt_form", OnsephereBoltFormView);
});

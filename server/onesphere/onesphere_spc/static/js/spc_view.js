odoo.define("onesphere.spc.render", function (require) {
  "use strict";

  var FormView = require("web.FormView");
  const FormRenderer = require("web.FormRenderer");
  const SPCViewerController = require("onesphere.spc.controller");
  var viewRegistry = require("web.view_registry");

  var SPCViewerRenderer = FormRenderer.extend({
    init: function (parent, state, params) {
      this.charts = [];
      this._super.apply(this, arguments);
    },

    on_detach_callback: function () {
      this.charts.forEach((chart) => {
        window.removeEventListener("resize", chart.resize);
        chart.dispose();
      });
      this.charts = [];
      this._super.apply(this, arguments);
    },

    _renderTabPage: function (page, page_id) {
      var self = this;
      var $ret = this._super.apply(this, arguments);
      $ret.css({ width: "100%" });
      var $container = $ret.find("div.o_echarts").get(0);
      if (!!!$container) {
        return $ret;
      }
      var chart = echarts.getInstanceByDom($container);
      if (!!!chart) {
        //如果为初始化过这个容器作为echarts容器
        chart = echarts.init($container, null, { height: 600 });
        this.charts.push(chart);
        chart.on("click", function (params) {
          self.click_chart_data(params);
        });
        window.addEventListener("resize", chart.resize);
      }
      return $ret;
    },

    click_chart_data: function (params) {
      console.log(params);
    },

    render_pages: function (pages) {
      var self = this;
      _.map(pages, function (opts, selection) {
        var sel = "div." + selection;
        var ele = self.$el.find(sel).get(0);
        if (!!ele) {
          // 找到这个echarts DOM元素
          const charts = echarts.getInstanceByDom(ele);
          if (!!charts) {
            charts.setOption(opts, { notMerge: true }); // 如果有的话会删除之前所有的option
            charts.resize();
          }
        }
      });
    },

    _onNotebookTabChanged: function (evt) {
      var self = this;
      var selection = evt.target.hash; // 获取div id
      var ele = self.$el.find(selection).children("div.o_echarts").get(0);
      if (!!ele) {
        // 找到这个echarts DOM元素
        const charts = echarts.getInstanceByDom(ele);
        if (!!charts) {
          charts.resize();
        }
      }
      this._super.apply(this, arguments);
    },
  });

  var SPCFormView = FormView.extend({
    config: _.extend({}, FormView.prototype.config, {
      Controller: SPCViewerController,
      Renderer: SPCViewerRenderer,
    }),
  });

  viewRegistry.add("spc_form", SPCFormView);

  return SPCViewerRenderer;
});

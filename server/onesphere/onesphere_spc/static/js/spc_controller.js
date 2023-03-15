odoo.define("onesphere.spc.controller", function (require) {
  "use strict";

  const FormController = require("web.FormController");
  var core = require("web.core");

  var qweb = core.qweb;

  var defaultDateTimeFormat = "YYYY-MM-DD HH:mm:ss";

  function getStartEndDate(self, step, action) {
    var query_date_from = self.renderer.state.data["query_date_from"];
    var query_date_to = self.renderer.state.data["query_date_to"];
    var start,
      end = undefined;
    if (!query_date_from) {
      var d = moment(query_date_to).subtract(1, step).startOf("day");
      self.setData(self.handle, "query_date_from", d);
      query_date_from = d.format(defaultDateTimeFormat);
    }
    var query_date_from_local = moment.utc(query_date_from).local();
    var query_date_to_local = moment.utc(query_date_to).local();
    switch (action) {
      case "prev":
        var diff = query_date_to_local.diff(query_date_from_local, step);
        if (diff <= 0) {
          // start = moment(end).subtract(1, step).startOf('day');
          end = moment.utc(query_date_from).local();
        } else {
          end = query_date_to_local.subtract(1, step).startOf("day");
        }
        start = query_date_from_local.subtract(1, step).startOf("day");
        break;
      case "next":
        var diff = query_date_to_local.diff(query_date_from_local, step);
        if (diff <= 0) {
          // start = moment(end).subtract(1, step).startOf('day');
          start = moment.utc(query_date_to).local();
        } else {
          start = query_date_from_local.add(1, step).startOf("day");
        }
        end = query_date_to_local.add(1, step).startOf("day");
        break;
      case "this_week":
        query_date_to = moment(); //当天
        start = moment(query_date_to).startOf("week").startOf("day");
        end = moment(query_date_to).endOf("week").add(1, "days").startOf("day");
        break;
      case "this_month":
        query_date_to = moment(); //当天
        start = moment(query_date_to).startOf("month").startOf("day");
        end = moment(query_date_to)
          .endOf("month")
          .add(1, "days")
          .startOf("day");
        break;
      case "today":
        start = moment().startOf("date").startOf("day");
        end = moment().add(1, "days").startOf("day");
        break;
      default:
        console.error(action + " SPC Form Is Not Support!!!!");
        break;
    }
    console.log("start" + start.toISOString());
    console.log("end" + end.toISOString());
    return { query_date_from: start, query_date_to: end };
  }

  var SPCViewerController = FormController.extend({
    events: _.extend({}, FormController.prototype.events, {
      "click button.o_calendar_button_prev": "_onButtonNavigation",
      "click button.o_calendar_button_today": "_onButtonNavigation",
      "click button.o_calendar_button_this_week": "_onButtonNavigation",
      "click button.o_calendar_button_this_month": "_onButtonNavigation",
      "click button.o_calendar_button_next": "_onButtonNavigation",
      "click button.o_spc_button_query": "_onButtonQuerySPC",
    }),
    init: function (parent, model, renderer, params) {
      this._super.apply(this, arguments);
      this.step = "months";
    },

    canBeDiscarded: function (recordID) {
      return new Promise((resolve) => resolve(true)); //隐藏discard confirm提示窗口优化用户体验
    },

    _onButtonQuerySPC: function (ev) {},
    renderButtons: function ($node) {
      this.$buttons = $(qweb.render("SPCViews.buttons", { widget: this }));

      var self = this;
      var bindSPCViewButton = function (selector, func, arg1, arg2) {
        self.$buttons.on("click", selector, _.bind(func, self, arg1, arg2));
      };

      bindSPCViewButton(".o_calendar_button_days", this.changeStep, "days");
      bindSPCViewButton(".o_calendar_button_weeks", this.changeStep, "weeks");
      bindSPCViewButton(".o_calendar_button_months", this.changeStep, "months");

      this.$(".o_calendar_buttons").replaceWith(this.$buttons);
      this.changeStep(this.step);
    },

    _extractLastPartOfClassName(startClassName, classList) {
      var result;
      classList.forEach(function (value) {
        if (value && value.indexOf(startClassName) === 0) {
          result = value.substring(startClassName.length);
        }
      });
      return result;
    },

    _onButtonNavigation(jsEvent) {
      const action = this._extractLastPartOfClassName(
        "o_calendar_button_",
        jsEvent.currentTarget.classList
      );
      if (action) {
        this.doAction(action, jsEvent);
      }
    },

    doAction(action, ev) {
      var self = this;
      let od = getStartEndDate(self, self.step, action);
      if (!!od) {
        self.setData(self.handle, "query_date_from", od.query_date_from.utc());
        self.setData(self.handle, "query_date_to", od.query_date_to.utc());
      }
    },

    setData: function (dataPointID, field_name, value) {
      var self = this;
      self.trigger_up("field_changed", {
        dataPointID: dataPointID,
        changes: { [field_name]: value },
        onSuccess: function () {
          console.log("success");
        },
      });
    },

    changeStep(step) {
      var self = this;
      this.step = step;
      if (self.$buttons !== undefined) {
        self.$buttons.find(".active").removeClass("active");
        self.$buttons.find(".o_calendar_button_" + step).addClass("active");
      }
    },
  });

  return SPCViewerController;
});

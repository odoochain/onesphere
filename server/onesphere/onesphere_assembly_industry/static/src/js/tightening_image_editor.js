odoo.define('oneshare.tightening_image_editor', function (require) {
    'use strict';

    var fieldRegistry = require('web.field_registry');

    var core = require('web.core');

    var _lt = core._lt;

    var _t = core._t;

    const OneshareImageEditor = require('oneshare.modal_image_editor');

    var OneshareTighteningImageEditor = OneshareImageEditor.extend({
        description: _lt("Tightening Image Editor"),
        template: 'OneshareTighteningImageEditor',
        events: _.extend({}, OneshareImageEditor.prototype.events, {
            'click .js_add_mask': '_onAddMask',
            'click .js_remove_mask': '_onRemoveLastMask',
            'click .js_remove_all_mask': '_onRemoveAllMask',
            'click .js_save': '_saveAllMask',
        }),

        markPoints: [],

        _notifyInfo: function (type, title, message, sticky) {
            return this.displayNotification({
                type: type,
                title: title,
                message: message,
                sticky: sticky,
            });
        },

        // _setOne2ManyField: function (field, list, resolve, reject) {
        //     var self = this;
        //     var viewType = this.record.viewType;
        //     if (list && this.record.fieldsInfo[viewType] && this.record.fieldsInfo[viewType][field]) {
        //         list.forEach(function (item) {
        //             var changes = {};
        //             changes[field] = {
        //                 operation: 'CREATE',
        //                 data: item,
        //             };
        //
        //             self.trigger_up('field_changed', {
        //                 dataPointID: self.dataPointID,
        //                 changes: changes,
        //                 onSuccess: resolve,
        //                 onFailure: reject,
        //             });
        //         });
        //     }
        // },

        // _resolve: function () {
        //     var self = this;
        //     self._notifyInfo('success', _t("Success"), _t('Save Tightening Points Success!'), false);
        // },
        //
        // _reject: function () {
        //     var self = this;
        //     self._notifyInfo('danger', _t("Error"), _t('Save Tightening Points Error!'), false);
        // },

        _saveAllMask: function () {
            var self = this;
            var active_id = this.recordData.res_record_id;
            var url = '/api/v1/tightening_work_step/';
            var markPoints = JSON.stringify(self.markPoints);
            try {
                // self.trigger_up('save_tightening_points', {
                //     dataPointID: self.dataPointID,
                //     changes: self.markPoints,
                //     onSuccess: self._resolve,
                //     onFailure: self._reject,
                // });
                $.ajax({
                    type: "PUT",
                    url: url.concat(active_id, '/opr_points_edit'),
                    timeout: 2000, //超时时间设置，单位毫秒
                    dataType: 'json',
                    data: markPoints,
                    beforeSend: function (xhr) {
                        xhr.setRequestHeader('Content-Type', 'application/json');
                        xhr.setRequestHeader('X-Org-Name', 'oneshare');
                    },
                }).done(function (resp) {
                    self._notifyInfo('success', _t("Success"), _t('Save Tightening Points Success!'), false);
                    self.do_action({'type': 'ir.actions.client', 'tag': 'reload'});
                }).fail(function (resp) {
                    self._notifyInfo('danger', _t("Error"), _t('Save Tightening Points Error!'), false);
                });
            } catch (e) {
                self._notifyInfo('danger', _t("Error"), e.message, false);
            }
        },

        init: function (field_manager, node) {
            this._super.apply(this, arguments);
            this.markPoints.splice(0, this.markPoints.length); //清空mark点位
        },

        inline_add_new_mask: function (top, left) {
            var self = this;
            var imgWidth = parseFloat(this.$el.find('#img').css('width'));
            var imgHeight = parseFloat(this.$el.find('#img').css('height'));
            var leftOffset = left || 0;
            var topOffset = top || 0;
            var t = _.str.sprintf('<div class="oe_mark_circle">%s</div>', _.str.escapeHTML(this.markPoints.length + 1));
            var e = $(t).css({
                'left': leftOffset ? "calc(" + leftOffset + "% - 10px)" : "calc(" + leftOffset + "%)",
                'top': topOffset ? "calc(" + topOffset + "% - 10px)" : "calc(" + topOffset + "%)",
                'z-index': "" + (this.markPoints.length + 1)
            }).appendTo(self.$el.find('#img_container'));

            interact('.oe_mark_circle').draggable({
                restrict: {
                    restriction: "parent",
                    endOnly: false,
                    elementRect: {top: 0, left: 0, bottom: 1, right: 1}
                },
                autoScroll: true,
                onmove: this.dragMoveListener.bind(this),
                onend: this.MarkerDragstop.bind(this),

            });
            this.markPoints.push({sequence: this.markPoints.length + 1, x_offset: left || 0, y_offset: top || 0});
        },


        _render: function () {
            var self = this;
            var activeModel = self.model;
            var active_id = self.recordData.res_record_id;
            if (!!!active_id) {
                //非已经创建的记录
                self._notifyInfo('danger', _t("Error"), '请先保存记录后进行图片编辑', false);
                self.trigger_up('do_parent_form_save'); //模拟点击保存按钮
                return;
            }
            try {
                this._super.apply(this, arguments);
                this._rpc({
                    model: 'oneshare.quality.point',
                    method: 'get_tightening_operation_points',
                    args: [active_id],
                }).then(function (result) {
                    _.each(result, function (ele) {
                        self.inline_add_new_mask(ele.y_offset, ele.x_offset);
                    })
                });
            } catch (e) {
                self._notifyInfo('danger', _t("Error"), e.message, false);
                console.error(e);
            }
        },

        dragMoveListener: function (event) {
            event.stopPropagation();
            var target = event.target;
            // keep the dragged position in the data-x/data-y attributes
            var currentX = (parseFloat(target.getAttribute('current-data-x')) || 0) + event.dx;
            var currentY = (parseFloat(target.getAttribute('current-data-y')) || 0) + event.dy;
            var totalX = (parseFloat(target.getAttribute('total-data-x')) || 0) + event.dx;
            var totalY = (parseFloat(target.getAttribute('total-data-y')) || 0) + event.dy;


            // translate the element
            target.style.webkitTransform =
                target.style.transform =
                    'translate(' + totalX + 'px, ' + totalY + 'px)';

            // update the posiion attributes

            target.setAttribute('total-data-x', totalX);
            target.setAttribute('total-data-y', totalY);
            target.setAttribute('current-data-x', currentX);
            target.setAttribute('current-data-y', currentY);
        },

        MarkerDragstop: function (event) {
            event.stopPropagation();
            var self = this;
            var idx = parseInt(event.target.textContent, 10) - 1;
            var imgWidth = parseFloat(this.$el.find('#img').css('width'));
            var imgHeight = parseFloat(this.$el.find('#img').css('height'));
            var circleWidth = 20;
            var circleHeight = 20;

            var target = event.target,
                // keep the dragged position in the data-x/data-y attributes
                x = (parseFloat(target.getAttribute('current-data-x')) || 0),
                y = (parseFloat(target.getAttribute('current-data-y')) || 0);

            self.markPoints[idx].x_offset = self.markPoints[idx].x_offset === 0 ?
                (imgWidth ? (x + circleWidth / 2) / imgWidth * 100 : 0) :
                (imgWidth ? self.markPoints[idx].x_offset + x / imgWidth * 100 : 0);
            self.markPoints[idx].y_offset = self.markPoints[idx].y_offset === 0 ?
                (imgHeight ? (y + circleHeight / 2) / imgHeight * 100 : 0) :
                (imgHeight ? self.markPoints[idx].y_offset + y / imgHeight * 100 : 0);
            target.setAttribute('current-data-x', 0);
            target.setAttribute('current-data-y', 0);
            // self.markPoints[idx].y_offset = imgHeight ? (ui.position.top + circleHeight / 2) / imgHeight * 100 : 0;
        },


        _onAddMask: function (ev) {
            ev.stopPropagation();
            var self = this;
            var t = _.str.sprintf('<div class="oe_mark_circle">%s</div>', _.str.escapeHTML(this.markPoints.length + 1));
            var e = $(t).css({
                'left': "" + 0 + "%",
                'top': "" + 0 + "%",
                'z-index': "" + (this.markPoints.length + 1)
            }).appendTo(self.$el.find('#img_container'));

            interact('.oe_mark_circle').draggable({
                restrict: {
                    restriction: "parent",
                    endOnly: false,
                    elementRect: {top: 0, left: 0, bottom: 1, right: 1}
                },
                autoScroll: true,
                onmove: this.dragMoveListener.bind(this),
                onend: this.MarkerDragstop.bind(this),
            });

            // e.on('draggable:stop',function(event, ui){console.log(event, ui)});
            this.markPoints.push({sequence: this.markPoints.length + 1, x_offset: 0, y_offset: 0});
        },

        _onRemoveLastMask: function (ev) {
            ev.stopPropagation();
            this.$('.oe_mark_circle:last').remove(); //添加是prepend
            this.markPoints.pop();
        },

        _onRemoveAllMask: function (ev) {
            if (!!ev) {
                ev.stopPropagation();
            }
            this.$('.oe_mark_circle').remove();
            this.markPoints.splice(0, this.markPoints.length);
        },

        destroy: function () {
            this._super.apply(this, arguments);
            this._onRemoveAllMask(null);
        },

    });
    fieldRegistry.add('oneshare_tightening_image_editor', OneshareTighteningImageEditor);

    return OneshareTighteningImageEditor;
});
;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
    'date'
], function ($, _, Backbone, gettext, Date) {
    'use strict';

    function formatDate(date) {
        return dateUTC(date).toString('MMM dd, yyyy');
    }

    function formatDateKOR(date) {
        return dateUTC(date).toString('yyyy년M월dd일');
    }

    // Return a date object using UTC time instead of local time
    function dateUTC(date) {
        return new Date(
            date.getUTCFullYear(),
            date.getUTCMonth(),
            date.getUTCDate(),
            date.getUTCHours(),
            date.getUTCMinutes(),
            date.getUTCSeconds()
        );
    }

    return Backbone.View.extend({

        tagName: 'li',
        templateId: '#result_item-tpl',
        className: 'courses-listing-item',

        initialize: function () {
            this.tpl = _.template($(this.templateId).html());
        },

        render: function () {
            var data = _.clone(this.model.attributes);
            var arrUniv = [['KHUk', 'KoreaUnivK', 'PNUk', 'SNUk', 'SKKUk', 'YSUk', 'EwhaK', 'POSTECHk', 'KAISTk', 'HYUk', 'KMOOC'],
            ['경희대학교','고려대학교','부산대학교','서울대학교','성균관대학교','연세대학교','이화여자대학교','포항공과대학교','한국과학기술원','한양대학교', 'K-MOOC']];
            for (var i=0; i <= arrUniv[0].length; i++) {
                if (data.org == arrUniv[0][i]) {
                    data.org = arrUniv[1][i];
                    break;
                }
            }
            data.start = formatDateKOR(new Date(data.start));
            data.enrollment_start = formatDate(new Date(data.enrollment_start));
            this.$el.html(this.tpl(data));
            return this;
        }

    });

});

})(define || RequireJS.define);
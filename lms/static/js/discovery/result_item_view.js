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
            //console.log("this.templateId = "+ this.templateId);
            this.tpl = _.template($(this.templateId).html());
        },

        render: function () {
            var data = _.clone(this.model.attributes);
            var arrUniv = [['KHUk', 'KoreaUnivK', 'PNUk', 'SNUk', 'SKKUk', 'YSUk', 'EwhaK', 'POSTECHk', 'KAISTk', 'HYUk', 'KMOOC', 'INHAuniversityK','KUMOHk','CUKk','BUFSk','JEJUk','KNUk','YeungnamUnivK','KonYangK','DKUK'],
            ['경희대학교','고려대학교','부산대학교','서울대학교','성균관대학교','연세대학교','이화여자대학교','포항공과대학교','한국과학기술원','한양대학교', 'K-MOOC','인하대학교','금오공과대학교','가톨릭대학교','부산외국어대학교','제주대학교','경북대학교','영남대학교','건양대학교','단국대학교']];

            for (var i=0; i <= arrUniv[0].length; i++) {
                if (data.org == arrUniv[0][i]) {
                    data.org = arrUniv[1][i];
                    break;
                }
            }
            data.start = formatDateKOR(new Date(data.start));
            data.enrollment_start = formatDate(new Date(data.enrollment_start));


            console.log("data == " + data);
            console.log("keys == " + Object.keys(data));
            console.log("end1 check == " + data.end);
            console.log("end2 check == " + data.enrollment_end);

            this.$el.html(this.tpl(data));
            return this;
        }

    });

});

})(define || RequireJS.define);
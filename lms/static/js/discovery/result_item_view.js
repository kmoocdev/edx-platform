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

            //data.start = formatDateKOR(new Date(data.start));
            //data.enrollment_start = formatDate(new Date(data.enrollment_start));

            var d = new Date().toISOString().slice(0,16);

            //if(data.end != null && data.end.slice(0,16) < d && data.enrollment_end == null)
            //    data.archive = true;
            //else
            //    data.archive = false;

            var start = data.start ? data.start.slice(0,16) : null;
            var end = data.end ? data.end.slice(0,16) : null;
            var enrollment_start = data.enrollment_start ? data.enrollment_start.slice(0,16) : null;
            var enrollment_end = data.enrollment_end ? data.enrollment_end.slice(0,16) : null;

            //console.log(data.id + ": d = " + d + " : es =  " + enrollment_start + " : ee = " + enrollment_end + " : st =  " + start + " : en =  " + end);
            //
            //console.log("1: " + enrollment_start <= d);
            //console.log("2: " + enrollment_end == null);
            //console.log("3: " + d <= enrollment_end);
            //console.log("4: " + start <= d);
            //console.log("5: " + d < end);

            if(enrollment_start <= d && (enrollment_end == null || d <= enrollment_end) && d < start){
                data.state = '개강 예정';
            }else if(enrollment_start <= d && (enrollment_end == null || d <= enrollment_end) && start <= d  && end != null && end != "" && d < end){
                data.state = '진행 강좌 (수강 가능)';
            }else if(start < d && d < end && enrollment_end < d){
                data.state = '진행 강좌';
            }else if(end < d && (enrollment_end == null || enrollment_end < d)){
                data.state = '종료 강좌 (수강 가능)';
            }else if(end < d){
                data.state = '종료 강좌';
            }else {
                data.state = '';
            }

            data.start = formatDateKOR(new Date(data.start));
            data.enrollment_start = formatDate(new Date(data.enrollment_start));

            this.$el.html(this.tpl(data));
            return this;
        }

    });

});

})(define || RequireJS.define);
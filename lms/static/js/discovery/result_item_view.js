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
            var arrUniv = {
                'KHUk':'경희대학교',
                'KoreaUnivK':'고려대학교',
                'PNUk':'부산대학교',
                'SNUk':'서울대학교',
                'SKKUk':'성균관대학교',
                'YSUk':'연세대학교',
                'EwhaK':'이화여자대학교',
                'POSTECHk':'포항공과대학교',
                'KAISTk':'한국과학기술원',
                'HYUk':'한양대학교',
                'KYUNGNAMUNIVk':'경남대학교',
                'DGUk':'대구대학교',
                'SMUCk':'상명대학교(천안)',
                'SSUk':'성신여자대학교',
                'SejonguniversityK':'세종대학교',
                'SookmyungK':'숙명여자대학교',
                'YeungnamUnivK':'영남대학교',
                'UOUk':'울산대학교',
                'INHAuniversityK':'인하대학교',
                'CBNUk':'전북대학교',
                'GachonUnivK':'가천대학교',
                'KonYangK':'건양대학교',
                'DonggukK':'동국대학교',
                'DSUk':'동신대학교',
                'MokwonK':'목원대학교',
                'SMUk':'상명대학교(서울)',
                'UOSk':'서울시립대',
                'CAUk':'중앙대학교',
                'CNUk':'충남대학교',
                'HGUk':'한동대학교',
                'HallymK':'한림대학교',
                'KONGJUk':'공주대학교',
                'KUMOHk':'금오공과대학교',
                'DKUK':'단국대학교',
                'BUFSk':'부산외국어대학교',
                'SYUk':'삼육대학교',
                'KNUk':'경북대학교',
                'CUKk':'가톨릭대학교',
                'JEJUk':'제주대학교',
                'SKP.KAISTk':'서울대, 한국과학기술원, 포항공대',
                'SKP.SNUk':'서울대, 한국과학기술원, 포항공대',
                'SKP.POSTECHk':'서울대, 한국과학기술원, 포항공대'
            };

            for (var key in arrUniv) {
                if (data.org == key) {
                    data.org = arrUniv[key];
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
                data.state = 'Starting Soon';
            }else if(enrollment_start <= d && (enrollment_end == null || d <= enrollment_end) && start <= d  && end != null && end != "" && d < end){
                data.state = 'Current (Join Now)';
            }else if(start < d && d < end && enrollment_end < d){
                data.state = 'Current (Registration closed)';
            }else if(end < d && (enrollment_end == null || d <= enrollment_end)){
                data.state = 'Archived (Join Now)';
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
;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
    'js/discovery/result_item_view'
], function ($, _, Backbone, gettext, ResultItemView) {
   'use strict';

    return Backbone.View.extend({

        el: 'section.courses',
        $window: $(window),
        $document: $(document),

        initialize: function () {
            this.$list = this.$el.find('.courses-listing');
            this.attachScrollHandler();
        },

        render: function () {
            this.$list.empty();
            this.renderItems();
            return this;
        },

        renderNext: function () {
            this.renderItems();
            this.isLoading = false;
        },

        renderItems: function () {
            var latest = this.collection.latestModels();

            var dupllist = new Array();
            var courses  = new Array();
            var courses1 = new Array();
            var courses2 = new Array();
            var courses3 = new Array();
            var courses4 = new Array();

            var d = new Date().toISOString().slice(0,16)

            //강좌 시작일(desc) > 등록 시작일(asc) 순으로 정렬
            latest.sort(function(a,b){
                return a.attributes.start == b.attributes.start ? a.attributes.enrollment_start > b.attributes.enrollment_start : a.attributes.start < b.attributes.start;
            });


            for(var i=0;i<latest.length;i++){

                var id = latest[i].id;
                var display_name = latest[i].attributes.content.display_name;
                var start = latest[i].attributes.start;
                var end = latest[i].attributes.end;
                var enrollment_start = latest[i].attributes.enrollment_start;
                var enrollment_end = latest[i].attributes.enrollment_end;

                //console.log('enrollment_start: ' + enrollment_start + " , enrollment_end: " + enrollment_end);

                //console.log(display_name);

                //if(dupllist.indexOf(display_name) < 0)
                //    dupllist.push(display_name);
                //else
                //    continue;

                //console.log(display_name + " : " + start);
                if(id == 'course-v1:KMOOC+DEMOk+2015_1') {
                    courses4.push(latest[i]);
                }else if(enrollment_start == null || enrollment_start == "" || enrollment_start > d || start == null || start == ""){
                    continue;
                }else if(enrollment_start.slice(0, 16) <= d && (enrollment_end == null || d <= enrollment_end.slice(0, 16)) && d < start.slice(0, 16)){
                    courses1.push(latest[i]);
                }else if(enrollment_start.slice(0, 16) <= d && (enrollment_end == null || d <= enrollment_end.slice(0, 16)) && d > start.slice(0, 16) && end != null && end != "" && d < end.slice(0, 16)){
                    courses2.push(latest[i]);
                }else{
                    courses3.push(latest[i]);
                }
            }

            courses1.sort(function(a,b){
                if(a.attributes.start.slice(0, 16) > b.attributes.start.slice(0, 16))
                    return 1;
                if(a.attributes.start.slice(0, 16) < b.attributes.start.slice(0, 16))
                    return -1;
                return 0;
            });
            courses2.sort(function(a,b){
                if(a.attributes.start.slice(0, 16) < b.attributes.start.slice(0, 16))
                    return 1;
                if(a.attributes.start.slice(0, 16) > b.attributes.start.slice(0, 16))
                    return -1;
                return 0;
            });
            courses3.sort(function(a,b){
                if(a.attributes.start.slice(0, 16) < b.attributes.start.slice(0, 16))
                    return 1;
                if(a.attributes.start.slice(0, 16) > b.attributes.start.slice(0, 16))
                    return -1;
                return 0;
                //return a.attributes.start.slice(0, 16).replace(/-/gi,"").replace(/:/gi,"").replace(/T/gi,"") < b.attributes.start.slice(0, 16).replace(/-/gi,"").replace(/:/gi,"").replace(/T/gi,"");
            });

            //var i=0;
            //while(i<courses1.length){
            //    console.log('1. ' + courses1[i].attributes.content.display_name + " : " + courses1[i++].attributes.start.slice(0, 16));
            //}
            //i = 0;
            //while(i<courses2.length){
            //    console.log('2. ' + courses2[i].attributes.content.display_name + " : " + courses2[i++].attributes.start.slice(0, 16));
            //}
            //i = 0;
            //while(i<courses3.length){
            //    console.log('3. ' + courses3[i].attributes.content.display_name + " : " + courses3[i].attributes.start.slice(0, 16) + " : " + courses3[i++].attributes.start.slice(0, 16).replace(/-/gi,"").replace(/:/gi,"").replace(/T/gi,""));
            //}

            courses = courses.concat(courses1, courses2, courses3, courses4);

            latest = courses;

            var items = latest.map(function (result) {
                var item = new ResultItemView({ model: result });
                return item.render().el;
            }, this);

            this.$list.append(items);
        },

        attachScrollHandler: function () {
            this.nextScrollEvent = true;
            this.$window.on('scroll', this.scrollHandler.bind(this));
        },

        scrollHandler: function () {
            if (this.nextScrollEvent) {
                setTimeout(this.throttledScrollHandler.bind(this), 400);
                this.nextScrollEvent = false;
            }
        },

        throttledScrollHandler: function () {
            if (this.isNearBottom()) {
                this.scrolledToBottom();
            }
            this.nextScrollEvent = true;
        },

        isNearBottom: function () {
            var scrollBottom = this.$window.scrollTop() + this.$window.height();
            var threshold = this.$document.height() - 200;
            return scrollBottom >= threshold;
        },

        scrolledToBottom: function () {
            if (this.thereIsMore() && !this.isLoading) {
                this.trigger('next');
                this.isLoading = true;
            }
        },

        thereIsMore: function () {
            return this.collection.hasNextPage();
        }

    });

});


})(define || RequireJS.define);

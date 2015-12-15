;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
    'js/discovery/facets_view',
    'js/discovery/facet_view'
], function ($, _, Backbone, gettext, FacetsView, FacetView) {
    'use strict';

    return Backbone.View.extend({

        el: '.search-facets',

        tagName: 'div',
        templateId: '#search_facets_list-tpl',
        className: 'facets',
        facetsTypes: {},
        moreLessLinksTpl: '#more_less_links-tpl',

        events: {
            'click li': 'addFacet',
            'click .show-less': 'collapse',
            'click .show-more': 'expand',
        },

        initialize: function (facetsTypes) {
            if(facetsTypes) {
                this.facetsTypes = facetsTypes;
            }
            this.tpl = _.template($(this.templateId).html());
            this.moreLessTpl = _.template($(this.moreLessLinksTpl).html());
            this.$el.html(this.tpl());
            this.facetViews = [];
            this.$facetViewsEl = this.$el.find('.search-facets-lists');
        },

        render: function () {
            return this;
        },

        collapse: function(event) {
            var $el = $(event.currentTarget),
                $more = $el.siblings('.show-more'),
                $ul = $el.parent('div').siblings('ul');

            event.preventDefault();

            $ul.addClass('collapse');
            $el.addClass('hidden');
            $more.removeClass('hidden');
        },

        expand: function(event) {
            var $el = $(event.currentTarget),
                $ul = $el.parent('div').siblings('ul'),
                facets = $ul.find('li').length,
                itemHeight = 34;

            event.preventDefault();

            $el.addClass('hidden');
            $ul.removeClass('collapse');
            $el.siblings('.show-less').removeClass('hidden');
        },

        addFacet: function(event) {
            if($("#clear-all-filters"))
                $("#clear-all-filters").click();

            event.preventDefault();
            var $target = $(event.currentTarget);
            var value = $target.find('.facet-option').data('value');
            var name = $target.find('.facet-option').data('text');
            var data = {type: $target.data('facet'), query: value, name: name};
            this.trigger('addFilter', data);
        },

        displayName: function(name, term){
            if(this.facetsTypes.hasOwnProperty(name)) {
                if(term) {

                    if (typeof this.facetsTypes[name].terms !== 'undefined') {
                        return this.facetsTypes[name].terms.hasOwnProperty(term) ? this.facetsTypes[name].terms[term] : term;
                    }
                    else {
                        var arrWords = [ ['KHUk','KoreaUnivK', 'PNUk', 'SNUk', 'SKKUk', 'YSUk', 'EwhaK', 'POSTECHk', 'KAISTk', 'HYUk', 'KMOOC'],
                        ['경희대학교','고려대학교','부산대학교','서울대학교','성균관대학교','연세대학교','이화여자대학교','포항공과대학교','한국과학기술원','한양대학교', 'K-MOOC'] ];
                        for (var i=0; i < arrWords[0].length; i++) {
                            if (term == arrWords[0][i]) {
                                return arrWords[1][i];
                            } 
                        }
                    }
                }
                else if(this.facetsTypes[name].hasOwnProperty('name')) {
                    //return this.facetsTypes[name]['name'];
                    return '기관명';
                }
                else {
                    return name;
                }
            }
            else{
                if (term) {
                    var arrWords = [ ['khuk','koreaunivk', 'pnuk', 'snuk', 'skkuk', 'ysuk', 'ewhak', 'postechk', 'kaistk', 'hyuk', 'kmooc'],
                    ['경희대학교','고려대학교','부산대학교','서울대학교','성균관대학교','연세대학교','이화여자대학교','포항공과대학교','한국과학기술원','한양대학교', 'K-MOOC'] ];
                    for (var i=0; i < arrWords[0].length; i++) {
                        if (term == arrWords[0][i]) {
                            return arrWords[1][i];
                        }
                    }
                }
                else {
                    return '기관명';
                }

            }
        },

        renderFacets: function(facets) {
            var self = this;
            // Remove old facets
            $.each(this.facetViews, function(key, facetsList) {
                facetsList.remove();
            });
            self.facetViews = [];
            // Render new facets
            $.each(facets, function(name, stats) {
                if (name=="org") {
                    var facetsView = new FacetsView();
                    self.facetViews.push(facetsView);
                    self.$facetViewsEl.append(facetsView.render(name, self.displayName(name), stats).el);
                    $.each(stats.terms, function(term, count) {
                        var facetView = new FacetView();
                        facetsView.$views.append(facetView.render(name, self.displayName(name, term), term, count).el);
                        facetsView.list.push(facetView);
                    });
                    if(_.size(stats.terms) > 9) {
                        facetsView.$el.append(self.moreLessTpl());
                    }
                }
            });
        },

    });

});

})(define || RequireJS.define);

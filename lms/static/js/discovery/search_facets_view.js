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

                        if(!arrUniv.hasOwnProperty(term))
                             return term;

                        for (var key in arrUniv) {
                            if (term == key) {
                                return arrUniv[key];
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

                    if(!arrUniv.hasOwnProperty(term))
                         return term;

                    for (var key in arrUniv) {
                        if (term == key) {
                            return arrUniv[key];
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

            //console.log('facets ==> ' + facets);
            //console.log('facets ==> ' + facets.length);
            //$.each(facets, function(name, stats) {
            //    console.log(name +":"+stats.count +":" + stats.terms.count);
            //});

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

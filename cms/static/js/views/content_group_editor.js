/**
 * This class defines an editing view for content groups.
 * It is expected to be backed by a Group model.
 */
define([
    'js/views/list_item_editor', 'underscore'
],
function(ListItemEditorView, _) {
    'use strict';

    var ContentGroupEditorView = ListItemEditorView.extend({
        tagName: 'div',
        className: 'content-group-edit collection-edit',
        events: {
            'submit': 'setAndClose',
            'click .action-cancel': 'cancel'
        },

        initialize: function() {
            ListItemEditorView.prototype.initialize.call(this);
            this.template = this.loadTemplate('content-group-editor');
        },

        getTemplateOptions: function() {
            return {
                id: this.model.escape('id'),
                name: this.model.escape('name'),
                index: this.model.collection.indexOf(this.model),
                isNew: this.model.isNew(),
                usage: this.model.get('usage'),
                uniqueId: _.uniqueId()
            };
        },

        setValues: function() {
            var value = this.$('input').val().trim()
            value = value.replace(/<script/gi,"<noscript").replace(/\/script/gi,"\/noscript");
            this.model.set({name: value});
            return this;
        },

        getSaveableModel: function() {
            return this.model.collection.parents[0];
        }
    });

    return ContentGroupEditorView;
});

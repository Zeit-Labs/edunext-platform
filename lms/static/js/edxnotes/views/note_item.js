;(function (define, undefined) {
'use strict';
define([
    'jquery', 'underscore','backbone', 'js/edxnotes/utils/template',
    'js/edxnotes/utils/logger'
], function ($, _, Backbone, templateUtils, NotesLogger) {
    var NoteItemView = Backbone.View.extend({
        tagName: 'article',
        className: 'note',
        id: function () {
            return 'note-' + _.uniqueId();
        },
        events: {
            'click .note-excerpt-more-link': 'moreHandler',
            'click .reference-unit-link': 'unitLinkHandler',
        },

        initialize: function (options) {
            this.template = templateUtils.loadTemplate('note-item');
            this.logger = NotesLogger.getLogger('note_item', options.debug);
            this.listenTo(this.model, 'change:is_expanded', this.render);
        },

        render: function () {
            var context = this.getContext();
            this.$el.html(this.template(context));

            return this;
        },

        getContext: function () {
            return $.extend({
                message: this.model.getNoteText()
            }, this.model.toJSON());
        },

        toggleNote: function () {
            var value = !this.model.get('is_expanded');
            this.model.set('is_expanded', value);
        },

        moreHandler: function (event) {
            event.preventDefault();
            this.toggleNote();
        },

        unitLinkHandler: function (event) {
            var REQUEST_TIMEOUT = 2000;
            event.preventDefault();
            this.logger.emit('edx.student_notes.used_unit_link', {
                'note_id': this.model.get('id'),
                'component_usage_id': this.model.get('usage_id')
            }, REQUEST_TIMEOUT).always(_.bind(function () {
                this.redirectTo(event.target.href);
            }, this));
        },

        redirectTo: function (uri) {
            window.location = uri;
        },

        remove: function () {
            this.logger.destroy();
            Backbone.View.prototype.remove.call(this);
            return this;
        }
    });

    return NoteItemView;
});
}).call(this, define || RequireJS.define);

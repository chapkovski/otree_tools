/*!
 * Copyright (c) 2012 Ben Olson (https://github.com/bseth99/jquery-ui-extensions)
 * jQuery UI LabeledSlider @VERSION
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use,
 * copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following
 * conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 *
 * Depends:
 *  jquery.ui.core.js
 *  jquery.ui.widget.js
 *  jquery.ui.mouse.js
 *  jquery.ui.slider.js
 */

/* a very minor update done by Philipp Chapkovski, to provide an option to draw secondary ticks w/out labels*/
function floatSafeRemainder(val, step) {
    val = parseFloat(val);
    step = parseFloat(step);
    var valDecCount = (val.toString().split('.')[1] || '').length;
    var stepDecCount = (step.toString().split('.')[1] || '').length;
    var decCount = valDecCount > stepDecCount ? valDecCount : stepDecCount;
    var valInt = parseInt(val.toFixed(decCount).replace('.', ''));
    var stepInt = parseInt(step.toFixed(decCount).replace('.', ''));
    return (valInt % stepInt) / Math.pow(10, decCount);
}

(function ($, undefined) {


    $.widget("ui.labeledslider", $.ui.slider, {

        version: "@VERSION",

        options: {
            tickInterval: 0,
            tweenLabels: true,
            tickLabels: null,
            tickArray: [],
            secondaryTicks: true,
            showLabels: true,
            ndigits:0,
            suffix:''
        },

        uiSlider: null,
        tickInterval: 0,
        tweenLabels: true,

        _create: function () {

            this._detectOrientation();

            this.uiSlider =
                this.element
                    .wrap('<div class="ui-slider-wrapper ui-widget"></div>')
                    .before('<div class="ui-slider-labels">')
                    .parent()
                    .addClass(this.orientation)
                    .css('font-size', this.element.css('font-size'));

            this._super();

            this.element.removeClass('ui-widget')

            this._alignWithStep();

            if (this.orientation == 'horizontal') {
                this.uiSlider
                    .width(this.element.css('width'));
            } else {
                this.uiSlider
                    .height(this.element.css('height'));
            }
            if (this.options.showLabels) {
                this._drawLabels();
            }
        },

        _drawLabels: function () {

            var labels = this.options.tickLabels || {},
                $lbl = this.uiSlider.children('.ui-slider-labels'),
                dir = this.orientation == 'horizontal' ? 'left' : 'bottom',
                min = this.options.min,
                max = this.options.max,
                sectick = this.options.secondaryTicks,
                inr = this.tickInterval,
                cnt = ( max - min ),
                tickArray = this.options.tickArray,
                ta = tickArray.length > 0,
                stp = this.options.step,
                ndigits=this.options.ndigits,
                sf=this.options.suffix,
                label, pt,
                j = 0,
                i = 0;


            $lbl.html('');


            for (; j <= cnt; j += stp) {
                i = parseFloat(j).toFixed(ndigits);
                if (( !ta && floatSafeRemainder(i, inr) == 0 ) || ( ta && tickArray.indexOf(i + min) > -1 )) {
                    var lb_candidate = (parseFloat(parseFloat(i) + parseFloat(min)).toFixed(ndigits)).toString()+sf ;
                    label = labels[i + min] ? labels[i + min] : (this.options.tweenLabels ? lb_candidate : '');
                    $('<div>').addClass('ui-slider-label-ticks bold-tick')
                        .css(dir, (Math.round(( i / cnt ) * 10000) / 100) + '%')
                        .html('<span>' + ( label ) + '</span>')
                        .appendTo($lbl);

                }
                else {
                    if (floatSafeRemainder(i, stp) == 0 && sectick == true) {
                        $('<div>').addClass('ui-slider-label-ticks')
                            .css(dir, (Math.round(( i / cnt ) * 10000) / 100) + '%')
                            .appendTo($lbl);
                    }
                }
            }

        },

        _setOption: function (key, value) {

            this._super(key, value);

            switch (key) {

                case 'tickInterval':
                case 'tickLabels':
                case 'tickArray':
                case 'min':
                case 'max':
                case 'step':

                    this._alignWithStep();
                    this._drawLabels();
                    break;

                case 'orientation':

                    this.element
                        .removeClass('horizontal vertical')
                        .addClass(this.orientation);

                    this._drawLabels();
                    break;
            }
        },

        _alignWithStep: function () {
            if (this.options.tickInterval < this.options.step)
                this.tickInterval = this.options.step;
            else
                this.tickInterval = this.options.tickInterval;
        },

        _destroy: function () {
            this._super();
            this.uiSlider.replaceWith(this.element);
        },

        widget: function () {
            return this.uiSlider;
        }

    });

}(jQuery));
$(function () {
    $("#slider").slider({
        value: 100,
        min: 0,
        max: 500,
        step: 100,
        slide: function (event, ui) {
            $("#amount").val("$" + ui.value);
        }
    });
    $("#amount").val("$" + $("#slider").slider("value"));

    $("#slider2").slider({
        value: 100,
        min: 0,
        max: 500,
        step: 100,
        slide: function (event, ui) {
            $("#amount2").val("$" + ui.value);
        }
    });
    $("#amount2").val("$" + $("#slider2").slider("value"));
});

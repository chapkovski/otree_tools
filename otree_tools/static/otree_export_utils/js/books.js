$(function () {

    $(".js-create-book").click(function () {
        $.ajax({
            url: '/test_items/create/',
            type: 'get',
            dataType: 'json',
            beforeSend: function () {
                $("#modal-book").modal("show");
            },
            success: function (data) {
                $("#modal-book .modal-content").html(data.html_form);
            }
        });
    });

});

$("#modal-book").on("submit", ".js-book-create-form", function () {
    var form = $(this);
    $.ajax({
        url: form.attr("action"),
        data: form.serialize(),
        type: form.attr("method"),
        dataType: 'json',
        success: function (data) {
            if (data.form_is_valid) {
                console.log(data.html_book_list);
                 $("#book-table tbody").html(data.html_book_list);  // <-- Replace the table body
                 $("#modal-book").modal('hide');
            }
            else {
                $("#modal-book .modal-content").html(data.html_form);
            }
        }
    });
    return false;
});
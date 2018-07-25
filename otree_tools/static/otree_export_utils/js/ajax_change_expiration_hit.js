$(function () {

  $("#hit-delete").click(function () {
      console.log('deleting hit...');
    $.ajax({
      url: delete_hit_url,
      type: 'get',
      dataType: 'json',

      success: function (data) {
          console.log(data);
        $("div#hit_status").html(data);
      }
    });
  });

});
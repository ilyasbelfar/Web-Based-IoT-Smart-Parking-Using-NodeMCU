$(function() {
    var table = $('.logs_list').DataTable();

    minDateFilter = "";
    maxDateFilter = "";

 $(".daterange").daterangepicker({
    "format": "YYYY-MM-DD HH:mm:ss",
    "timePicker": true,
    "timePicker24Hour": true,
    "timePickerSeconds": true,
    "locale": {
        "format": "YYYY-MM-DD HH:mm:ss",
        "separator": " To ",
        "fromLabel": "From",
        "toLabel": "To",
    }
 });
 $(".daterange").on("apply.daterangepicker", function(ev, picker) {
  minDateFilter = Date.parse(picker.startDate);
  maxDateFilter = Date.parse(picker.endDate);
  
  $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
  var date = Date.parse(data[1]);

  if (
   (isNaN(minDateFilter) && isNaN(maxDateFilter)) ||
   (isNaN(minDateFilter) && date <= maxDateFilter) ||
   (minDateFilter <= date && isNaN(maxDateFilter)) ||
   (minDateFilter <= date && date <= maxDateFilter)
  ) {
   return true;
  }
  return false;
 });
 table.draw();
}); 


    new Chartist.Bar(
        "#totalParkingTimesChart .ct-chart", {
            labels: [
                "A",
                "B",
                "C",
                "D",
                "E",
                "F",
                "G",
                "H",
                "I",
                "J",
                "K",
                "L",
                "M",
                "N",
                "O",
                "P",
                "Q",
                "R",
                "S",
                "T"
            ],
            series: [
                [6, 3, 2, 5, 4, 7, 5, 7, 4, 5, 4, 7, 8, 3, 6, 4, 8, 6, 8, 6, 4]
            ]
        }, {
            low: 0,
            fullWidth: true,
            chartPadding: {
                top: 0,
                right: 0,
                bottom: 0,
                left: 0
            },
            axisX: {
                showLabel: false,
                showGrid: false,
                offset: 0
            },
            axisY: {
                showLabel: false,
                showGrid: false,
                offset: 0
            }
        }
    );


    new Chartist.Bar(
        "#totalMoneySpentChart .ct-chart", {
            labels: [
                "A",
                "B",
                "C",
                "D",
                "E",
                "F",
                "G",
                "H",
                "I",
                "J",
                "K",
                "L",
                "M",
                "N",
                "O",
                "P",
                "Q",
                "R",
                "S",
                "T"
            ],
            series: [
                [2, 4, 3, 6, 3, 5, 2, 7, 5, 3, 5, 6, 9, 4, 5, 1, 3, 5, 8, 3, 2]
            ]
        }, {
            low: 0,
            fullWidth: true,
            chartPadding: {
                top: 0,
                right: 0,
                bottom: 0,
                left: 0
            },
            axisX: {
                showLabel: false,
                showGrid: false,
                offset: 0
            },
            axisY: {
                showLabel: false,
                showGrid: false,
                offset: 0
            }
        }
    );

    if ($('.counter').length > 0) {
        $.each($('.counter'), function() {
            var count = $(this).data('count'),
            numAnim = new CountUp(this, 0, count);
            numAnim.start();
        });
    }

    $(":input").inputmask();

});
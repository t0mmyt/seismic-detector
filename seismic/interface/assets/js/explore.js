var app = angular.module('explore', ['ngUrlBind']);

app.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('{a');
    $interpolateProvider.endSymbol('a}');
}]);

app.controller('exploreCtrl', function($scope, $http, ngUrlBind) {
    $scope.evt = {};
    ngUrlBind($scope, 'evt')
    $scope.event = '';
    $scope.params = {
        absolute: false,
        bandpass: false,
        bandpassLow: 1,
        bandpassHigh: 20,
        sax: false,
        paaInt: 50,
        saxAlphabet: "abcdefg"
    };
    $scope.charts = [];

    $scope.renderChart = function (i) {
        $http({
            method: 'GET',
            url: '/sax/' + $scope.evt.id + '/view'
        }).then(function onSuccess(result) {
            $scope.charts[i] = c3.generate({
                bindto: "#chart_" + i,
                data: {
                    json: result.data,
                    keys: {
                        x: 't',
                        value: ['y']
                    }
                },
                axis: {
                    x: {
                        type: 'timeseries',
                        tick: {
                            format: function (e) {
                                var date = new Date(e);
                                return date.toISOString();
                            },
                            count: 5,
                            culling: { max: 5 }
                        }
                    }
                },
                point: {show: false},
                subchart: {show: true}
            })
        }, function onError(result) {
            console.log(result.status)
        })
    };

    if (typeof($scope.evt.id) !== 'undefined' && $scope.evt.id.length > 0) $scope.renderChart(1)
});
var app = angular.module('explore', ['ngUrlBind']);

app.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('{a');
    $interpolateProvider.endSymbol('a}');
}]);

app.controller('exploreCtrl', function($scope, $http, ngUrlBind) {
    $scope.evt = {};
    ngUrlBind($scope, 'evt');
    $scope.event = '';
    $scope.params = {
        offset: 0,
        length: 5000,
        absolute: false,
        bandpass: false,
        bandpassLow: 1,
        bandpassHigh: 20,
        sax: false,
        paaInt: 50,
        alphabet: "abcdefg"
    };
    $scope.charts = [];
    $scope.chartData = [];
    $scope.suffixTrees = [];
    $scope.selectedSuffixTree = "";

    $scope.renderChart = function (i) {
        $http({
            method: 'GET',
            url: '/api/sax/event/' + $scope.evt.id + '/view',
            params: $scope.params
        }).then(function onSuccess(result) {
            console.time("Rendering chart");
            $scope.chartData[i] = result.data;
            $scope.charts[i] = new Chart($("#chart_" + i), {
                type: 'line',
                data: {
                    datasets: [{
                        label: 'Z',
                        type: 'line',
                        pointRadius: 0,
                        borderColor: "LightSteelBlue",
                        borderWidth: 1.5,
                        fill: false,
                        data: $scope.chartData[i].original
                    },
                    {
                        label: 'PAA',
                        type: 'line',
                        steppedLine: true,
                        pointRadius: 0,
                        borderColor: "Red",
                        borderWidth: 2,
                        fill: false,
                        data: $scope.chartData[i].paa
                    }]
                },
                options: {
                    scales: {
                        xAxes: [{
                            type: 'time',
                            position: 'bottom',
                            time: {
                                parser: function (e) {
                                    return moment(e).utc()
                                }
                            }
                        }]
                    }
                }
            });
            console.timeEnd("Rendering chart")

        }, function onError(result) {
            console.log("Bad stuff happened: " + result.status_code)
        })
    };

    $scope.populateSuffixTrees = function () {
         $http.get("/api/suffix").then(function (result) {
             result.data.forEach(function (s) {
                 $scope.suffixTrees.push(s.description)
             });
         })
    };

    $scope.saveToTree = function () {
        $http({
            method: 'put',
            url: '/api/suffix/' + $scope.currentTreeId,
            data: {
                document: $scope.chartData[1].sax,
                description: $scope.evt
            }
        }).then(function (result) {
            console.log("Saving document to tree: " + result.status_code)
        })
    };

    if (typeof($scope.evt.id) !== 'undefined' && $scope.evt.id.length > 0) $scope.renderChart(1)
    $scope.populateSuffixTrees();
});
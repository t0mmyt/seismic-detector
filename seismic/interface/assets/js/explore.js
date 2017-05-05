var app = angular.module('explore', []);

app.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('{a');
    $interpolateProvider.endSymbol('a}');
}]);

app.controller('exploreCtrl', function($scope, $http) {
    $scope.params = {
        event: "",
        absolute: false,
        bandpass: false,
        bandpassLow: 1,
        bandpassHigh: 20,
        sax: false,
        paaInt: 50,
        saxAlphabet: "abcdefg"
    }
});
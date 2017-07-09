var app = angular.module('app', ['ngUrlBind']);

app.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('{a');
    $interpolateProvider.endSymbol('a}');
}]);

app.controller('MainCtrl', function($scope, $http, ngUrlBind) {
    $scope.currentTreeId = "";
    ngUrlBind($scope, 'currentTreeId');
    $scope.currentTree = null;
    $scope.currentDocs = [];
    $scope.trees = {};
    $scope.orderBy = "updated";
    $scope.reverse = false;
    $scope.query = "";
    $scope.queryResults = null;
    $scope.createParams = {};

    $scope.updateCurrentTree = function (tree) {
        $scope.trees.some(function (t) {
            if (t.id === tree) {
                $scope.currentTree = t;
                $scope.currentTreeId = t.id;
                return true;
            }
        });
        $http.get("/api/suffix/" + tree).then( function (result) {
            $scope.currentDocs = result.data;
            $scope.queryResults = null;
        });
    };

    $scope.updateTrees = function () {
        $http.get("/api/suffix/").then(function (result) {
            $scope.trees = result.data;
        }).then(function () {
            if ($scope.currentTreeId !== "") {
                $scope.updateCurrentTree($scope.currentTreeId);
            }
        })
    };

    $scope.runQuery = function (query) {
        $scope.query = query;
        $http({
            url: "/api/suffix/" + $scope.currentTree.id,
            params: {
                query: query
            }
        }).then(function (result) {
            $scope.parseQueryResults(result.data)
        });
    };

    $scope.createTree = function () {
        $http({
            method: 'post',
            url: "/api/suffix/",
            data: $scope.createParams
        }).then(function () {
            $scope.updateTrees()
        })
    };

    $scope.deleteTree = function (tree) {
        $http.delete("/api/suffix/" + tree).then(function () {
            $scope.updateTrees()
        })
    };

    $scope.parseQueryResults = function (results) {
        var matchList = Object.keys(results).sort(function (a, b) {
                return b.length - a.length
            });
        if (matchList.length > 5) {
            matchList = matchList.slice(0, 5)
        }
        $scope.queryResults = {
            order: matchList,
            data: results
        };
    };

    $scope.updateTrees();
});

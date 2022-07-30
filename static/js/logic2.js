const combinedData = "./Resources\\combinedData.csv";


d3.csv(combinedData).then(function(data){

    var combinedData = data;

    console.log(combinedData);

    let plotStates = [];

    for (let i=0; i < combinedData.length; i++) {
        row = combinedData[i];
        plotStates.push(row.State); 
    }

    console.log(plotStates);

    var StatesEdit = Array.from(new Set(plotStates));

    console.log(StatesEdit);

    StatesEdit.forEach((state) => {
        d3.select("#selDataset").append("option").text(state);
    })

    plotData = combinedData.filter(initial_data => initial_data.State === "Oregon");
    
    console.log(plotData);

    let plotReviews = [];
    let plotBeers = [];
    let plotCount = [];


    for (let i=0; i < plotData.length; i++) {
        row = plotData[i];
        var index = plotBeers.indexOf(row.beer_style);
        if( index >= 0 )        // if there are mutliple beer type
        {
            // console.log("index", index);
            plotReviews[index] += Number(row.review_overall); 
            plotCount[index]++;
            continue;
        }

        plotReviews.push(Number(row.review_overall));
        plotBeers.push(row.beer_style);
        plotCount.push(1);
    }

    // calculate the average
    for(let i = 0; i < plotReviews.length; i++) {
        plotReviews[i] /= plotCount[i];
    }

    // console.log(plotReviews);

    slicedReviews = plotReviews.slice(0,10).reverse();
    slicedBeers = plotBeers.slice(0,10).reverse();

    console.log(slicedReviews);
    console.log(slicedBeers);
    
    var trace1 = {
        x: slicedReviews,
        y: slicedBeers,
        type: "bar",
        orientation: "h"
    };

    var barData = [trace1];

    var barlayout = {
        title: `<b>Beer Style Reviews by State<b>`,
        xaxis: { title: "Average Review Score"},
        yaxis: {title: "Beer Style"},
        autosize: false,
        margin: {
            l: 300,
            r: 100
        }
    };

    Plotly.newPlot("bar", barData, barlayout);

    
    
    d3.select("#selDataset").on("change", updatePlot);
    console.log("selDataset");

    function updatePlot() {
        console.log("uupdate");
        var inputElement = d3.select("#selDataset");

        var inputValue = inputElement.property("value");
        console.log(inputValue);

        dataset = combinedData.filter(initial_data => initial_data.State === inputValue);

        console.log(dataset)

        plotReviews = [];
        plotBeers = [];
        plotCount = [];


        for (let i=0; i < dataset.length; i++) {
            row = dataset[i];

            var index = plotBeers.indexOf(row.beer_style);
            if( index >= 0 )        // if there are mutliple beer type
            {
                plotReviews[index] += Number(row.review_overall); 
                plotCount[index]++;
                continue;
            }

            plotReviews.push(Number(row.review_overall));
            plotBeers.push(row.beer_style);
            plotCount.push(1);
        }
    
        // calculate the average
        for(let i = 0; i < plotReviews.length; i++) {
            plotReviews[i] /= plotCount[i];
        }

        top10Reviews = plotReviews.slice(0,10).reverse();
        top10Beers = plotBeers.slice(0,10).reverse();

        Plotly.restyle("bar", "x", [top10Reviews]);
        Plotly.restyle("bar", "y", [top10Beers])

    }
    
});
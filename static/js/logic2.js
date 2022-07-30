const combinedData = "../../Resources/combinedData.csv";


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

    for (let i=0; i < plotData.length; i++) {
        row = plotData[i];
        if( plotBeers.includes(row.beer_style) )
            continue;
        plotReviews.push(row.review_overall);
        plotBeers.push(row.beer_style);
        
    }

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
        xaxis: { title: "Review Score"},
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


        for (let i=0; i < dataset.length; i++) {
            row = dataset[i];

            if( plotBeers.includes(row.beer_style) )
                continue;
            plotReviews.push(row.review_overall);
            plotBeers.push(row.beer_style);
        }

        top10Reviews = plotReviews.slice(0,10).reverse();
        top10Beers = plotBeers.slice(0,10).reverse();

        Plotly.restyle("bar", "x", [top10Reviews]);
        Plotly.restyle("bar", "y", [top10Beers])

    }
    
});
let score=0;
let rAF;
let nextF=[];
let cellSize=32;
let tetrominos={
    I:[
        [0,0,0,0],
        [1,1,1,1],
        [0,0,0,0],
        [0,0,0,0]
    ],
    J:[
        [0,0,0],
        [1,1,1],
        [0,0,1]
    ],
    L:[
        [0,0,0],
        [1,1,1],
        [1,0,0]
    ],
    O:[
        [1,1],
        [1,1]
    ],
    S:[
        [0,1,1],
        [1,1,0],
        [0,0,0]
    ],
    Z:[
        [1,1,0],
        [0,1,1],
        [0,0,0]
    ],
    T:[
        [0,1,0],
        [1,1,1],
        [0,0,0]
    ]};
let speed=20;
let canvas=document.querySelector("#game");
let game=canvas.getContext("2d");
let colors={I:"blue", J:"green", L:"red", O:"violet", S:"pink", T:"yellow", Z:"orange"};
let playField=[];
let names=['I', 'J', 'L', 'O', 'S', 'T', 'Z'];
let tet;
for(let i=0;i<20;i++){
    playField.push([]);
    for(let j=0;j<10;j++){
        playField[i].push(0);
    }
}
function getNextTet(){
    let num=nextF.shift();
    let name=names[num];
    let matrix=tetrominos[name];
    console.log(num)
    let col=5;
    let row=-1;
    nextF.push(getRandomInt());
    document.querySelector("#figures").innerHTML=names[nextF[0]]+" "+names[nextF[1]]+" "+names[nextF[2]];
    return {
        name: name,
        matrix: matrix,
        row: row,
        col: col
    }
}
function isValidMove(r,c,mat){
    for(let i=0;i<mat.length;i++){
        for(let j=0;j<mat.length;j++){
            if(mat[i][j]!=0){
                if(r+i>=playField.length || c+j>=playField.length || playField[r+i][c+j]!=0){
                    return false;
                }
            }
        }
    }
    return true;
}
function placeTet(){
    speed=20;
    for(let i=0;i<tet.matrix.length;i++){
        for(let j=0;j<tet.matrix.length;j++){
            if(tet.matrix[i][j]==1){
                if(i+tet.row<=0){
                    showGameOver();
                }
                playField[tet.row+i][tet.col+j]=tet.name;
            }
        }
    }
    tet=getNextTet();
    let s=0
    for(let i=0;i<playField.length;i++){
        let f=0;
        for(let j=0;j<10;j++){
            if(playField[i][j]!=0){
                f++;
            }
        }
        if(f==10){
            s++;
            for(let j=0;j<10;j++){
                playField[i][j]=0;
            }
            let j=i;
            for(;j>0;j--){
                for(let k=0;k<10;k++){
                    playField[j][k]=playField[j-1][k];
                }
            }
            for(let k=0;k<10;k++){
                playField[j][k]=0;
            }
        }
    }
    switch(s){
        case 1:
            score+=100;
            break;
        case 2:
            score+=300;
            break;
        case 3:
            score+=700;
            break;
        case 4:
            score+=1500;
            break;
    }
    document.querySelector("#score").innerHTML="Score: "+score;
}
let count=0;
function loop(){
    if(!play){
        return;
    }
    rAF = requestAnimationFrame(loop);
    game.clearRect(0,0,canvas.width,canvas.height);
    for(let i=0;i<20;i++){
        for(let j=0;j<10;j++){
            if(playField[i][j]!=0){
                let c=colors[playField[i][j]];
                game.fillStyle=c;
                game.fillRect(cellSize*j,cellSize*i,cellSize-1,cellSize-1);
                // game.fillRect(0,0,50,50);
            }
        }
    }

    if(count++>speed){
        count=0;
        tet.row++;
        if(!isValidMove(tet.row,tet.col,tet.matrix)){                                          
            tet.row--;
            placeTet();
        }
    }
    game.fillStyle=colors[tet.name];
    for(r=0;r<tet.matrix.length;r++){
        for(c=0;c<tet.matrix[0].length;c++){
            if(tet.matrix[r][c]!=0){
                game.fillRect(cellSize*(c+tet.col),cellSize*(r+tet.row),cellSize-1,cellSize-1);
            }
        }
    }
}
function getRandomInt(){    
    let rnd=-1;
    while(rnd<0 || rnd>=7){
        rnd=Math.floor(Math.random()*8);
    }
    return rnd;
}
let play=false;
function showGameOver(){
    play=false;
    game.fillStyle="white"
    game.font = '36px monospace';
    game.globalAlpha = 1;
    game.fillStyle = 'white';
    game.font = '36px monospace';
    game.textAlign = 'center';
    game.textBaseline = 'middle';
    // game.fillRect(0, canvas.height / 2 - 30, 100, 60);
    game.fillText("Game Over",100,600);
}
function rotate(mat){
    let newMat=[];
    for(let i=0;i<mat.length;i++){
        newMat.push([]);
        for(let j=0;j<mat.length;j++){
            newMat[i].push(0);
        }
    }
    for(let i=0;i<mat.length;i++){
        for(let j=0;j<mat.length;j++){
            newMat[j][mat.length-1-i]=mat[i][j];
        }
    }
    if(isValidMove(tet.row,tet.col,newMat)){
        tet.matrix=newMat;
    }
}

document.addEventListener("keydown", (e)=>{
    let key=e.which;
    switch(key){
        case 32: // space
            nextF=[];
            nextF.push(getRandomInt());
            nextF.push(getRandomInt());
            nextF.push(getRandomInt());
            tet=getNextTet();
            playField=[];
            for(let i=0;i<20;i++){
                playField.push([]);
                for(let j=0;j<10;j++){
                    playField[i].push(0);
                }
            }
            score=0;
            play=true;
            console.log("sp")
            console.log(playField)
            window.cancelAnimationFrame(rAF);
            rAF = requestAnimationFrame(loop);
            break;
        case 37: // left
            console.log("l")
            tet.col--;
            if(!isValidMove(tet.row,tet.col,tet.matrix)){
                tet.col++;
            }
            break;
        case 38: // up
            rotate(tet.matrix);
            console.log("u")
            break;
        case 40: // down
            console.log("d")
            speed=0;
            break;
        case 39: // right
            console.log("r")
            tet.col++;
            if(!isValidMove(tet.row,tet.col,tet.matrix)){
                tet.col--;
            }
            break;
        case 82: // r
            console.log("pause")
            if(play){
                play=false;
                window.cancelAnimationFrame(rAF);
            }
            else{
                play=true;
                rAF = requestAnimationFrame(loop);
            }
    }
})

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>

static unsigned char baseTable[64][2]={
{0,'A'},{1,'B'},{2,'C'},{3,'D'},{4,'E'},{5,'F'},{6,'G'},{7,'H'},{8,'I'},{9,'J'},
{10,'K'},{11,'L'},{12,'M'},{13,'N'},{14,'O'},{15,'P'},{16,'Q'},{17,'R'},{18,'S'},
{19,'T'},{20,'U'},{21,'V'},{22,'W'},{23,'X'},{24,'Y'},{25,'Z'},{26,'a'},{27,'b'},
{28,'c'},{29,'d'},{30,'e'},{31,'f'},{32,'g'},{33,'h'},{34,'i'},{35,'j'},{36,'k'},
{37,'l'},{38,'m'},{39,'n'},{40,'o'},{41,'p'},{42,'q'},{43,'r'},{44,'s'},{45,'t'},
{46,'u'},{47,'v'},{48,'w'},{49,'x'},{50,'y'},{51,'z'},{52,'0'},{53,'1'},{54,'2'},
{55,'3'},{56,'4'},{57,'5'},{58,'6'},{59,'7'},{60,'8'},{61,'9'},{62,'+'},{63,'/'}
};

static int ansLen=0;

void printAns(char* ans){
	for(int i=0; i<ansLen; i++){
		printf("%c",ans[i]);
	}
}

char getBaseChar(char code){
	for(int i=0; i<64; i++){
		if(code==baseTable[i][0]){
			return baseTable[i][1];
		}
	}
	return 0;
}

char getBaseCode(char symbol){
	for(int i=0; i<64; i++){
		if(symbol==baseTable[i][1]){
			return baseTable[i][0];
		}
	}
	return 0;
}

void printHelp(){
	printf("Usage: mybase64 [-Ddh] [-b num] [-i in_file] [-o out_file]\n");
}

char* getCode(FILE* file){
	char* ans=malloc(1024*sizeof(char));
	if(!ans){
		printf("Memory error\n");
		exit(1);
	}
	int len=1024;
	int i=1;
	int c;
	char buf=0;
	while((c=getc(file))!=EOF){
		//printf("\nc %d\n",c);
		for(int j=0;j<8;j++, i++){
			buf=(buf<<1)|((c>>((8-i%8)%8))&1);
			//printf("\n%d\n",buf);
			if(i%6==0){
				if(i/6>=len){
					len*=2;
					ans=realloc(ans,len);
					if(!ans){
						printf("Memory error\n");
						exit(1);
					}
				}
				ans[i/6-1]=getBaseChar(buf);
				//printf("\nwr %d\n",buf);
				buf=0;
			}
		}	
	}
	if(i/8%3>0){
		for(;i%6!=0;i++){
			buf=buf<<1;
		}
		buf=buf<<1;
		if(i/6>=len){
			len*=2;
			ans=realloc(ans,len);
			if(!ans){
				printf("Memory error\n");
				exit(1);
			}
		}
		ans[i/6-1]=getBaseChar(buf);
		buf=0;
		for(;i/8%3!=0;i+=6){
			if(i/6+1>=len){
				len*=2;
				ans=realloc(ans,len);
				if(!ans){
					printf("Memory error\n");
					exit(1);
				}	
			}
			ans[i/6]='=';
		}
	}
	ans[i/6]='\0';
	ansLen=i/6;
	//printf("ans is %s len is %lu\n",ans,strlen(ans));
	return ans;
}

char* getDecode(FILE* file){
	char* ans=malloc(1024*sizeof(char));
	if(!ans){
		printf("Memory error\n");
		exit(1);
	}
	int len=1024;
	int i=1;
	int c;
	char buf=0;
	char code;
	int eq=0;
	while((c=getc(file))!=EOF){
		if(c=='='){eq++;}
		code=getBaseCode(c);
		for(int j=1; j<=6; j++,i++){
			buf=(buf<<1)|((code>>(6-j))&1);
			if(i%8==0){
				if(i/8>=len){
					len*=2;
					ans=realloc(ans,len);
					if(!ans){
						printf("Memory error\n");
						exit(1);
					}
				}
				ans[i/8-1]=buf;
				buf=0;
			}
		}		
	}
	ans[i/8-eq]='\0';
	ansLen=i/8-eq;
	return ans;
}

void printWithBreaks(char* ans, int breakCount){
	for(int i=0; i<ansLen;i++){
		printf("%c",ans[i]);
		if((i+1)%breakCount==0 && i+1!=ansLen){
			printf("\n");
		}
	}
}

int main(int argc, char* argv[]){
	char fd=0;
	char fi=0;
	char fb=0;
	char fo=0;
	char fh=0;
	char consoleOutput=1;
	char* inputFileName="-";
	char* outFileName="-";
	int breakCount=0;
	int opt;
	while((opt=getopt(argc,argv,"b:Ddhi:o:"))!=-1){
		switch(opt){
			case 'b':
				fb=1;
				errno=0;
				char* endptr;
				breakCount=strtol(optarg,&endptr,10);
				if(errno!=0 || endptr==optarg || *endptr!='\0')
				{printf("Invalid argument\n");printHelp();return 1;}
				break;
			case 'D':
				fd=1;
				break;
			case 'd':
				fd=1;
				break;
			case 'h':
				fh=1;
				break;
			case 'i':
				fi=1;
				inputFileName=optarg;
				break;
			case 'o':
				fo=1;
				outFileName=optarg;
				break;
			default:
				printHelp();
				return 1;
		}
	}
	if(fh==1){
		printHelp();
		return 0;
	}
	FILE* inFile;
	FILE* outFile;
	if(fi==0 || (strlen(inputFileName)==1 && inputFileName[0]=='-')){
		inFile=stdin;
	}
	else{
		inFile=fopen(inputFileName,"r");
		if(!inFile){
			printf("Fail to open file\n");
			return 1;
		}
	}
	char* ans=NULL;
	if(fd==0){
		ans=getCode(inFile);
	}
	else{
		ans=getDecode(inFile);
	}
	if(fo==1 && !(strlen(outFileName)==1 && outFileName[0]=='-')){
		consoleOutput=0;
		outFile=freopen(outFileName,"w",stdout);
		if(!outFile){
			printf("Fail to create file\n");
			return 1;
		}
	}
	if(fb==1 && breakCount!=0){
		printWithBreaks(ans,breakCount);
	}
	else{
		printAns(ans);
	}
	fclose(inFile);
	fclose(outFile);
	free(ans);
	if(consoleOutput){
		printf("\n");
	}
	return 0;
}

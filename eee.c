#include<unistd.h>
#include<stdio.h>
void main(){
        fork();
        printf("the pid is %d ",getpid());

}

package com.example.demo.exercise;

/**
 * 测试类
 *
 * @author dzm
 * @create 2018-08-22 18:25
 **/
public class Test {
    public static void main(String[] args) {
        String[] strings = {"1","2"};
      printArray(strings);

    }

    public static <E> void printArray(E[] inputArray){
        for(E e : inputArray){
            System.out.printf("%s",e);
        }
    }

}

package com.example.demo.exercise;

import java.util.ArrayList;

/**
 * 测试类
 *
 * @author dzm
 * @create 2018-08-22 18:25
 **/
public class Test {
    public static void main(String[] args) {
        ArrayList<Common>  allStudents = new ArrayList<>();
        ArrayList<Common>  boyStudents = new ArrayList<>();
        for (int i = 0; i < 10 ; i++) {
            Common  bean = new Common(i,"name is "+i,"address is "+i);
            allStudents.add(bean);

        }


        for (int i = 0; i < 5 ; i++) {
            Common  bean = new Common(i,"name is "+i,"address is "+i);
            boyStudents.add(bean);

        }

        System.out.println("allStudents.size()------before-------------->"+allStudents.size());
        System.out.println("remove result : "+allStudents.removeAll(boyStudents));
        System.out.println("allStudents.size()-------after-------------->"+allStudents.size());


    }

}

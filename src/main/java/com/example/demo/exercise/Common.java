package com.example.demo.exercise;

import lombok.Data;

/**
 * 通用测试类
 *
 * @author dzm
 * @create 2018-11-29 17:12
 **/
@Data
public class Common {
    private int id;
    private String name;
    private String address;

    public Common(int id, String name, String address) {
        this.id = id;
        this.name = name;
        this.address = address;
    }

}

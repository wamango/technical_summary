package com.example.demo.ddd;

/**
 * @author : dengzhiming
 * create at:  2021/1/28  11:17 上午
 * @description:
 */
public class User {
    private String phone;

    private String userId;

    public User(String phone,String userId){
        this.phone = phone;
        this.userId = userId;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }
}
package com.example.demo.ddd;


/**
 * @author : dengzhiming
 * create at:  2021/1/28  11:17 上午
 * @description:
 */
public class UserDTO {
    private String userName;

    private String userId;

    private String type;

    public String getUserName() {
        return userName;
    }

    public void setUserName(String userName) {
        this.userName = userName;
    }

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }
}
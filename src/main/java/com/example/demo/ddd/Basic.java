package com.example.demo.ddd;



/**
 * @author : dengzhiming
 * create at:  2021/1/28  11:17 上午
 * @description:
 */

public class Basic {

    private String roleType;

    public Basic(String roleType){
        this.roleType = roleType;
    }

    public String getRoleType() {
        return roleType;
    }

    public void setRoleType(String roleType) {
        this.roleType = roleType;
    }
}
package com.example.demo.domain.base;

import lombok.Data;

import java.util.Date;

/**
 * 品牌和机型关系表
 *
 * @author dzm
 * @create 2018-09-21 10:28
 **/
@Data
public class BrandModel {
    /**
     * 主键
     */
    private int autoId;

    /**
     * 应用号
     */
    private String appId;

    /**
     * 品牌号
     */
    private String brandId;

    /**
     * 机构号
     */
    private String brhId;

    /**
     * 操作系统类型
     */
    private String osType;

    /**
     * 机型
     */
    private String model;

    /**
     * 机型名称
     */
    private String modelName;

    /**
     * 状态 0 不可用；1 可用
     */
    private String status;
    /**
     * 创建时间
     */
    private Date createTime;

    /**
     * 更新时间
     */
    private Date updateTime;
}

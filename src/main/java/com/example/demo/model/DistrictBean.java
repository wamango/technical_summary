package com.example.demo.model;

import com.google.common.collect.Lists;
import com.google.common.collect.Sets;
import lombok.Data;
import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.lang.math.NumberUtils;

import java.io.Serializable;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Data
public class DistrictBean implements Serializable {

    /**
     * 编号
     *
     * @mbggenerated
     */
    private Long code;

    /**
     * 名称
     *
     * @mbggenerated
     */
    private String name;

    /**
     * 阿语名称
     *
     * @mbggenerated
     */
    private String arName;

    /**
     * 手机区号
     *
     * @mbggenerated
     */
    private String phoneAreaCode;

    /**
     * 父节点
     *
     * @mbggenerated
     */
    private Integer parentId;

    /**
     * 深度
     */
    private Integer level;

    private List<DistrictBean> children;


    /**
     * 查询树形结构类目数据
     * @param dept
     * @return
     */
    public static List<DistrictBean> tree(int dept, List<DistrictBean> list){
        //非顶级类目集合
        List<DistrictBean> districtBeanList = list.stream().filter(e->e.getParentId()!=0).collect(Collectors.toList());
        //顶级类目集合
        List<DistrictBean> topList = list.stream().filter(e->e.getParentId()==0).collect(Collectors.toList());
        if(CollectionUtils.isNotEmpty(districtBeanList)){
            //过滤条件set,指定set大小为非顶级类目集合的大小
            Set<Long> set = Sets.newHashSetWithExpectedSize(districtBeanList.size());
            //循环顶级类目插入子类目
            topList.forEach(districtBean -> {
                getChild(districtBean, districtBeanList, dept, set);
            });
                return topList;
        }
        return null;
    }

    /**
     * 递归获取子类目
     * @param districtBean
     * @param districtBeans
     * @param dept
     * @param set
     */
    public static void getChild(DistrictBean districtBean,List<DistrictBean> districtBeans,int dept,Set<Long> set){
        //过滤树的深度
        if(districtBean.getLevel()<dept || dept == 0){
            List<DistrictBean> childList = Lists.newArrayList();
            districtBeans.stream()
                    //判断是否已循环过当前对象
                    .filter(c->!set.contains(c.getCode()))
                    //判断是否父子关系
                    .filter(c-> NumberUtils.compare(c.getParentId(),districtBean.getCode())==0)
                    //set集合大小不超过districtBeans大小
                    .filter(c->set.size()<=districtBeans.size())
                    .forEach(c->{
                        //放入set，递归循环时可以跳过这个子类目
                        set.add(c.getCode());
                        //获取当前类目的子类目
                        getChild(c,districtBeans,dept,set);
                        //加入子类目集合
                        childList.add(c);
                    });
            districtBean.setChildren(childList);
        }
    }

}

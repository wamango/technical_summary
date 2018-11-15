package com.example.demo.mapper.base;


import com.example.demo.domain.base.BrandModel;

import java.util.List;

/**
 * 品牌机型表
 * @author fjy
 */
public interface BrandModelMapper {
	/**
	 * 查询品牌机型表
	 * @param brandModel
	 * @return
	 */
	List<BrandModel> queryBrandModel(BrandModel brandModel);


}

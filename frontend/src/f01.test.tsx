import {cleanup,fireEvent,render,screen} from '@testing-library/react'
import {afterEach,describe,it,expect} from 'vitest'
import App from './App'

afterEach(cleanup)

describe('F01 new review',()=>{
  it('uses controlled selects and the approved defaults',()=>{
    const {container}=render(<App/>)
    expect((screen.getByLabelText('内容类型') as HTMLSelectElement).value).toBe('产品体验')
    expect((screen.getByLabelText('内容目标') as HTMLSelectElement).value).toBe('品牌认知')
    expect((screen.getByLabelText('表达风格') as HTMLSelectElement).value).toBe('真实自然')
    expect(screen.getByPlaceholderText('例如：皇家美素佳儿')).toBeTruthy()
    expect(screen.getByText('审核依据')).toBeTruthy()
    expect(screen.getByText('AI 已识别本次审核任务')).toBeTruthy()
    expect(screen.getByText('正常优化')).toBeTruthy()
    expect(container.querySelectorAll('.btn-primary')).toHaveLength(1)
  })

  it('keeps advanced settings collapsed and persona automatic',()=>{
    render(<App/>)
    const details=screen.getByText('高级设置').closest('details') as HTMLDetailsElement
    expect(details.open).toBe(false)
    expect((screen.getByLabelText('AI 自动识别') as HTMLInputElement).checked).toBe(true)
    expect(screen.queryByLabelText('Persona 输入')).toBeNull()
  })

  it('edits, saves, and summarizes the review basis',()=>{
    render(<App/>)
    fireEvent.click(screen.getByText('查看 / 编辑审核依据'))
    expect(screen.getByRole('dialog',{name:'编辑审核依据'})).toBeTruthy()
    fireEvent.click(screen.getByLabelText('品牌名称统一'))
    fireEvent.click(screen.getByLabelText('内容结构'))
    fireEvent.click(screen.getByText('+ 添加自定义规则'))
    fireEvent.change(screen.getByLabelText('规则名称'),{target:{value:'结尾提示'}})
    fireEvent.change(screen.getByLabelText('规则说明'),{target:{value:'结尾增加自然提示'}})
    fireEvent.click(screen.getByText('添加规则'))
    expect(screen.getByText('结尾提示')).toBeTruthy()
    fireEvent.click(screen.getByText('保存本次审核依据'))
    expect(screen.queryByRole('dialog',{name:'编辑审核依据'})).toBeNull()
    expect(screen.getByText('v1.0 · 11 条')).toBeTruthy()
    expect(screen.getByText('5 项')).toBeTruthy()
    expect(screen.getByText('1 条')).toBeTruthy()
  })

  it('explains why the primary CTA is disabled',()=>{
    render(<App/>)
    expect(screen.getByText('请先输入待审核内容。')).toBeTruthy()
    expect((screen.getByText('确认并开始审核') as HTMLButtonElement).disabled).toBe(true)
  })
})

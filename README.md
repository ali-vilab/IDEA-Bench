# IDEA-Bench: How Far are Generative Models from Professional Designing?

<p align="center">
    <img src="./assets/tasks_vis.png" width="100%" height="100%">
</p>

<font size=3><div align='center' > [[🍎 Project Page]()] [[📖 arXiv Paper](https://arxiv.org/abs/2412.11767)] [[🤗 Dataset](https://huggingface.co/datasets/JasiLiang/IDEA-Bench)] [[⚔️ Arena (coming soon)]()]  </div></font>

---

## 🔥 News

* **`2024.12.17`** Paper is available on Arxiv. Dataset is available on Hugging Face. The code for automated evaluation is coming soon! 

## 👀 Contents

- [IDEA-Bench Overview](#idea-bench-overview)
- [Dataset License](#dataset-license)
- [MLLM Evaluation](#mllm-evaluation)
- [Arena Leaderboard](#leaderboard)
- [Citation](#citation)


## IDEA-Bench Overview

**IDEA-Bench** (***I**ntelligent **D**esign **E**valuation and **A**ssessment **B**enchmark*) is a comprehensive and pioneering benchmark designed to advance the capabilities of image generation models toward professional-grade applications. It addresses the gap between current generative models and the demanding requirements of professional image design through robust evaluation across diverse tasks.

### Task Coverage
IDEA-Bench encompasses **100 professional image generation tasks** and **275 specific cases**, systematically categorized into five major types:
1. **Text to Image (T2I):** Generate single images from text prompts.
2. **Image to Image (I2I):** Transform or edit input images based on textual guidance.
3. **Multi-image to Image (Is2I):** Create a single output image from multiple input images.
4. **Text to Multi-image (T2Is):** Generate multiple images from a single text prompt.
5. **(Multi-)image to Multi-image (I(s)2Is):** Create multiple output images from one or more input images.

<p align="center">
    <img src="./assets/sunburst-tasks.png" width="90%" height="100%">
</p>

### Evaluation Framework
- **Binary Scoring Items:** Incorporates **1,650 binary scoring items** to ensure precise, objective evaluations of generated images.
- **MLLM-Assisted Assessment:** Includes a **representative subset of 18 tasks** with enhanced criteria for automated assessments, where MLLM are leveraged to transform evaluations into image understanding tasks, surpassing traditional metrics like FID and CLIPScore in capturing aesthetic quality and contextual relevance.

<p align="center">
    <img src="./assets/pipeline.png" width="100%" height="100%">
</p>


## Dataset License

**License**:
The images and datasets included in this repository are subject to the terms outlined in the [LICENSE](LICENSE) file. Please refer to the file for details on usage restrictions.


## MLLM Evaluation

<p align="center">
    <img src="./assets/mllm_leader.png" width="80%" height="80%">
</p>

Code for automated evaluation is coming soon. 


## Leaderboard 

Learderboard based on **Arena** is coming soon. 


## Citation

If you find our work helpful for your research, please consider citing our work.   

```bibtex
@misc{liang2024ideabenchfargenerativemodels,
      title={IDEA-Bench: How Far are Generative Models from Professional Designing?}, 
      author={Chen Liang and Lianghua Huang and Jingwu Fang and Huanzhang Dou and Wei Wang and Zhi-Fan Wu and Yupeng Shi and Junge Zhang and Xin Zhao and Yu Liu},
      year={2024},
      eprint={2412.11767},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2412.11767}, 
}
```

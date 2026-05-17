<template>
  <el-table
    :data="tableData"
    border
    style="width: 100%"
    row-key="id"
    :default-sort="{ prop: 'final_score', order: 'descending' }"
  >
    <el-table-column type="expand">
      <template #default="props">
        <div v-if="props.row.ok" :class="$style.reasoningWrapper">
          <h4>AI Reasoning</h4>
          <p :class="$style.reasoningText">
            {{ props.row.details.reasoning }}
          </p>

          <div :class="$style.detailedScores">
            <el-tag type="success"
              >Semantic: {{ props.row.details.semantic_similarity }}</el-tag
            >
            <el-tag type="warning" class="ml-2"
              >LLM Judge: {{ props.row.details.llm_judge_score }}</el-tag
            >
          </div>
        </div>
        <div v-else :class="$style.reasoningWrapper">
          <el-alert
            title="Error during analysis"
            type="error"
            :description="props.row.error"
            show-icon
          />
        </div>
      </template>
    </el-table-column>

    <el-table-column label="Vacancy" min-width="200" show-overflow-tooltip>
      <template #default="scope">
        <router-link
          :to="{ name: 'vacancy-view', params: { id: scope.row.vacancy_id } }"
          target="_blank"
          :class="$style.docLink"
        >
          {{ scope.row.vacancyName }}
        </router-link>
      </template>
    </el-table-column>

    <el-table-column label="Resume" min-width="200" show-overflow-tooltip>
      <template #default="scope">
        <router-link
          :to="{ name: 'resume-view', params: { id: scope.row.resume_id } }"
          target="_blank"
          :class="$style.docLink"
        >
          {{ scope.row.resumeName }}
        </router-link>
      </template>
    </el-table-column>

    <el-table-column label="Status" width="100" align="center">
      <template #default="scope">
        <el-tag :type="scope.row.ok ? 'success' : 'danger'">
          {{ scope.row.ok ? "Success" : "Error" }}
        </el-tag>
      </template>
    </el-table-column>

    <el-table-column
      prop="final_score"
      label="Score"
      width="180"
      sortable
      align="center"
    >
      <template #default="scope">
        <el-progress
          v-if="scope.row.ok"
          :percentage="scope.row.final_score"
          :color="scoreColors"
        />
        <span v-else>-</span>
      </template>
    </el-table-column>

    <el-table-column width="60" align="center">
      <template #default="scope">
        <el-button
          type="danger"
          :icon="Close"
          circle
          text
          size="small"
          @click="$emit('remove-row', scope.row)"
        />
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup lang="ts">
import { Close } from "@element-plus/icons-vue";

defineProps<{
  tableData: any[];
}>();

defineEmits<{
  (e: "remove-row", row: any): void;
}>();

const scoreColors = [
  { color: "#f56c6c", percentage: 40 },
  { color: "#e6a23c", percentage: 70 },
  { color: "#5cb87a", percentage: 100 },
];
</script>

<style module>
.reasoningWrapper {
  padding: 15px 30px;
  background-color: #fafafa;
  border-left: 4px solid #409eff;
  border-radius: 4px;
  margin: 10px 20px;
}
.reasoningWrapper h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #303133;
}
.reasoningText {
  white-space: pre-wrap;
  line-height: 1.6;
  color: #606266;
  font-size: 14px;
  margin-bottom: 15px;
}
.detailedScores {
  display: flex;
  gap: 10px;
}

.docLink {
  color: #409eff;
  text-decoration: none;
  font-weight: 500;
}
.docLink:hover {
  text-decoration: underline;
}
</style>
